"""Normalize sensor results for a common run overview, independent of its UI.

Descriptive statistics and numeric availability describe the recorded data.
"""

import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
from uuid import uuid4

from .sensor_catalog import SENSORS
from .gear_timing import TOLERANCE
from .signal_checks import SCREENED_SENSORS, evaluate_screening

RESULT_LABELS = {"review": "Review", "no_findings": "No findings",
                 "not_assessed": "Not assessed", "not_logged": "Not logged"}


def _numeric_data(run, channel):
    values, missing, invalid = [], 0, 0
    for row in run["data"]:
        raw = row.get(channel, "")
        if raw is None or not str(raw).strip():
            missing += 1
            values.append(None)
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = math.nan
        if not math.isfinite(value):
            invalid += 1
            values.append(None)
        else:
            values.append(value)
    finite = [value for value in values if value is not None]
    return values, {
        "total_samples": len(values), "numeric_samples": len(finite),
        "missing_samples": missing, "invalid_samples": invalid,
        "numeric_fraction": len(finite) / len(values) if values else None,
        "minimum": min(finite) if finite else None,
        "median": statistics.median(finite) if finite else None,
        "maximum": max(finite) if finite else None,
    }


def _gear_result(analysis):
    if analysis["findings"]:
        more = len(analysis["findings"]) - 1
        return "review", analysis["findings"][0]["title"] + (f"; {more} more finding(s)." if more else ".")
    assessed = any(check["outcome"] in ("not_triggered", "not_applicable")
                   and check["assessment"] != "unavailable" for check in analysis["checks"])
    if analysis["overall"]["status"] == "insufficient_evidence" or not assessed:
        return "not_assessed", analysis["overall"]["summary"]
    notes = len(analysis.get("notes", []))
    suffix = f" {notes} informational transition note(s)." if notes else ""
    return "no_findings", "No findings from completed gear checks; assessment is limited." + suffix


def build_run_report(run, timing, gear_report):
    """Adapt the existing gear result and include all nine requested channels.

    Values retain one entry per CSV row. None represents missing/invalid data,
    never a fabricated zero. Chart rendering must respect those gaps.
    """
    total = len(run["data"])
    timed = timing.get("available", False)
    axis = list(timing["seconds"]) if timed else list(range(total))
    gap_after = []
    if timed and timing["basis"] == "recorded" and len(axis) > 1:
        intervals = [end - start for start, end in zip(axis, axis[1:])]
        factor = gear_report["analysis_settings"]["rules"]["maximum_gap_factor"]
        typical = statistics.median(intervals)
        gap_after = [index for index, interval in enumerate(intervals)
                     if interval > typical * factor + TOLERANCE]
    sensors = []
    for definition in SENSORS:
        sensor = dict(definition)
        candidates = [sensor["channel"], *sensor.get("aliases", [])]
        matches = [name for name in candidates if name in run["channels"]]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous channels for {sensor['name']}: {', '.join(matches)}")
        if matches:
            sensor["channel"] = matches[0]
        present = bool(matches)
        values, summary = _numeric_data(run, sensor["channel"]) if present else ([], None)
        sensor.update({"logged": present, "unit": run["units"].get(sensor["channel"], ""),
                       "values": values, "data_summary": summary, "checks": [],
                       "findings": [], "notes": [], "limitations": [], "analysis": None})
        if not present:
            status, observation, scope = "not_logged", "Channel absent from this CSV.", "Unavailable"
        elif sensor["id"] == "gear":
            analysis = copy.deepcopy(gear_report)
            status, observation = _gear_result(analysis)
            scope = ("Insufficient evidence" if analysis["overall"]["status"] == "insufficient_evidence"
                     else "Limited gear checks")
            sensor.update({"analysis": analysis, "checks": analysis["checks"],
                           "findings": analysis["findings"], "notes": analysis.get("notes", []),
                           "limitations": analysis["limitations"]})
        elif sensor["id"] in SCREENED_SENSORS:
            status, observation, scope = evaluate_screening(sensor, run, timing, gap_after)
        else:
            status, scope = "not_assessed", "Rules not implemented"
            observation = "Data available; sensor checks have not been implemented."
            if summary["missing_samples"] or summary["invalid_samples"]:
                observation = (f"{summary['missing_samples']} missing, {summary['invalid_samples']} invalid readings; "
                               "sensor checks have not been implemented.")
            sensor["limitations"] = ["No sensor-specific detection rules have been run."]
        sensor.update({"status": status, "status_label": RESULT_LABELS[status],
                       "assessment_scope": scope, "main_observation": observation})
        sensors.append(sensor)
    counts = {status: sum(sensor["status"] == status for sensor in sensors) for status in RESULT_LABELS}
    basis = timing.get("basis", "unavailable") if timed else "sample_index"
    note = ("Estimated from the CSV header; evenly spaced rows are assumed. Source dropouts cannot be verified."
            if basis == "estimated" else "Recorded timestamps; lines break at detected timestamp gaps."
            if basis == "recorded" else timing.get("reason", "Usable timing is unavailable; sample indices are shown."))
    return {
        "schema_version": "1.0", "report_type": "sensor_suite",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": copy.deepcopy(gear_report["source"]),
        "summary": {"sensor_types": 8, "channel_count": len(sensors), "counts": counts,
                    "finding_count": sum(len(sensor["findings"]) for sensor in sensors),
                    "note": "Findings indicate evidence to review, not confirmed sensor failures. Numeric availability is not a health score."},
        "timing": {"basis": basis, "unit": "s" if timed else "sample",
                   "sample_rate_hz": timing.get("sample_rate_hz"), "axis": axis,
                   "gap_after_sample": gap_after, "note": note,
                   "first_to_last_span": axis[-1] - axis[0] if axis else None},
        "sensors": sensors,
        "limitations": ["Checks cover gear, throttle, coolant and intake air temperature.",
                        "The throttle and temperature thresholds are provisional screening settings.",
                        "Statistics describe this recording and are not approved operating limits.", note],
    }


def format_run_report(report):
    lines = ["\nSENSOR RUN REPORT", f"File: {report['source']['path']}",
             f"Timing: {report['timing']['basis']} | Measurement rows: {report['source']['measurement_rows']}",
             f"{'Sensor':<26} {'Result':<15} Numeric readings"]
    for sensor in report["sensors"]:
        data = sensor["data_summary"]
        numeric = f"{data['numeric_samples']}/{data['total_samples']}" if data else "—"
        lines.append(f"{sensor['name']:<26} {sensor['status_label']:<15} {numeric}")
    counts = report["summary"]["counts"]
    lines += [f"\nChannels to review: {counts['review']} | Not assessed: {counts['not_assessed']} | Not logged: {counts['not_logged']}",
              report["summary"]["note"]]
    for sensor in report["sensors"]:
        for finding in sensor["findings"]:
            lines.append(f"{finding['id']}: {finding['message']}")
    lines += ["\n" + message for message in report["limitations"]]
    return "\n".join(lines)


def save_run_report(report, directory=None):
    """Save a standalone, offline HTML view and matching strict JSON data."""
    from .run_report_html import render_run_report

    json_text = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
    html_text = render_run_report(report)
    source = Path(report["source"]["path"])
    directory = Path(directory).expanduser() if directory is not None else source.parent / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    stem = f"{source.stem}.sensors.{stamp}.{uuid4().hex[:8]}"
    paths = {extension: (directory / f"{stem}.{extension}").resolve() for extension in ("json", "html")}
    for extension, content in (("json", json_text + "\n"), ("html", html_text)):
        with paths[extension].open("x", encoding="utf-8") as file:
            file.write(content)
    return paths
