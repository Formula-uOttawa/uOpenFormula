"""One serializable gear report shared by the terminal, plot, and saved file."""

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .gear_analyzer import summarize_gear, find_gear_observation_intervals
from .gear_run import evaluate_no_shift_run
from .gear_quality import evaluate_gear_quality
from .gear_states import build_gear_states
from .gear_transitions import evaluate_gear_transitions
from .timing import time_intervals


def gear_label(code):
    return {-1: "Reverse", 0: "Neutral"}.get(code, f"Gear {code:g}")


def _finding(item, check_id, run, timing):
    start = item["start_sample"]
    end = max(item["end_sample"], item["activation_sample"])
    timed = timing["available"]
    times = timing.get("seconds", [])
    location = {
        "start_sample": start, "end_sample": end,
        "activation_sample": item["activation_sample"],
        "time_basis": timing.get("basis", "unavailable"),
        "start_seconds": times[start] if timed else None,
        "end_seconds": times[end] if timed else None,
        "elapsed_span_seconds": times[end] - times[start] if timed else None,
    }
    # Preserve small raw windows around the boundaries, not a duplicate CSV.
    total = len(run["data"])
    indices = sorted(set(range(max(0, start - 2), min(total, start + 3)))
                     | set(range(max(0, end - 2), min(total, end + 3))))
    samples = [{"sample_index": index, "raw_gear": run["data"][index]["Gear Position"],
                "seconds": times[index] if timed else None} for index in indices]
    is_global = check_id == "whole_run_no_shift"
    return {
        "check_id": check_id, "severity": item.get("severity", "review"),
        "category": item.get("category", "transition_pattern"),
        "scope": "whole_recording" if is_global else "local_event",
        "title": item.get("kind", f"Recorded gear change: {item.get('from_gear')} to {item.get('to_gear')}"),
        "message": item.get("message", item.get("reason", "")),
        "location": location,
        "rule_version": item["rule_version"], "rule_status": item["rule_status"],
        "evidence": {"rule_result": copy.deepcopy(item), "sample_window": samples},
        "suggested_action": item.get("suggested_action") or (
            "Confirm whether this recording was expected to include gear changes."
            if is_global else "Inspect the highlighted readings and any independent shift evidence."
        ),
    }


def _evidence_sample_count(findings):
    """Count the union of evidence windows without counting overlaps twice."""
    merged = []
    for finding in sorted(findings, key=lambda item: item["location"]["start_sample"]):
        start, end = finding["location"]["start_sample"], finding["location"]["end_sample"]
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start + 1 for start, end in merged)


def analyze_gear(run, timing, rules, shifts_expected=None):
    statistics = summarize_gear(run)
    states = build_gear_states(run, rules["confirmation_samples"], rules["maximum_forward_gear"])
    transitions = evaluate_gear_transitions(states, timing, rules)
    quality = evaluate_gear_quality(run, timing, rules)
    whole_run = evaluate_no_shift_run(states, rules, shifts_expected=shifts_expected, timing=timing, run=run)
    observations = find_gear_observation_intervals(run)
    observations.setdefault("intervals", [])
    total = len(run["data"])

    checks = [{
        "id": "forward_sequence", "name": "Large recorded gear changes",
        "assessment": "unavailable", "outcome": "unassessed",
        "finding_count": len(transitions["findings"]),
        "message": transitions.get("reason", ""),
    }]
    if transitions["available"]:
        skipped = (transitions["unassessed"] + transitions["neutral_not_checked"]
                   + transitions["reverse_not_checked"])
        checks[0].update({
            "assessment": "partial" if skipped else "complete",
            "outcome": "review" if transitions["findings"] else "not_triggered",
            "comparison_count": len(transitions["transitions"]),
            "unassessed_comparison_count": len(skipped),
            "message": (f"Review code differences of at least {rules['large_jump_code_difference']}, "
                        f"with both endpoint plateaus lasting {rules['large_jump_endpoint_seconds']:g} s. "
                        "Intermediate confirmed gears are preserved; smaller skips are notes."),
        })
        if not transitions["findings"] and len(skipped) == len(transitions["transitions"]):
            checks[0]["outcome"] = "unassessed" if skipped else "not_applicable"

    whole_assessed = whole_run["available"] and whole_run["assessment"] != "insufficient_evidence"
    checks.append({
        "id": "whole_run_no_shift", "name": "Whole-run gear variation",
        "assessment": "complete" if whole_assessed else "unavailable",
        "outcome": (
            "unassessed" if not whole_assessed else "review" if whole_run["findings"]
            else "not_applicable" if whole_run["assessment"] == "no_confirmed_changes"
            else "not_triggered"
        ),
        "finding_count": len(whole_run["findings"]), "message": whole_run["message"],
    })
    checks.append({
        "id": "gear_signal_quality", "name": "Persistent unusable gear data",
        "assessment": ("partial" if quality.get("timestamp_gap_count") else "complete") if quality["available"] else "unavailable",
        "outcome": "review" if quality["findings"] else "not_triggered" if quality["available"] else "unassessed",
        "finding_count": len(quality["findings"]), "message": quality.get("message", quality.get("reason", "")),
    })

    findings = [_finding(item, "forward_sequence", run, timing) for item in transitions["findings"]]
    findings += [_finding(item, "whole_run_no_shift", run, timing) for item in whole_run["findings"]]
    findings += [_finding(item, "gear_signal_quality", run, timing) for item in quality["findings"]]
    findings.sort(key=lambda item: (item["location"]["start_sample"], item["check_id"]))
    for number, finding in enumerate(findings, 1):
        finding["id"] = f"GEAR-{number:03d}"

    notes = []
    for number, item in enumerate(transitions["notes"], 1):
        note = _finding({**item, "kind": f"Gear transition note: {item['from_gear']} to {item['to_gear']}",
                         "severity": "info", "category": "transition_note",
                         "rule_version": rules["version"], "rule_status": rules["status"]},
                        "forward_sequence", run, timing)
        note["id"] = f"GEAR-NOTE-{number:03d}"
        notes.append(note)

    limitations = [f"Forward gears 1–{rules['maximum_forward_gear']} are a configurable user-provided assumption.",
                   "Rule settings are provisional and not validated against labelled faults.",
                   "A valid recorded gear code does not establish that the sensor was correct."]
    if not timing["available"]:
        limitations.append(timing.get("reason", "Usable timing is unavailable."))
    elif timing["basis"] == "estimated":
        limitations.append("Times are estimated from the header rate; uniform sampling is assumed and source dropouts cannot be verified.")
    if transitions["available"]:
        if transitions["reverse_not_checked"]:
            limitations.append("Reverse transitions are observations; numerical forward-gear jump distance does not apply.")
        if transitions["unassessed"]:
            limitations.append(f"{len(transitions['unassessed'])} comparison(s) lack sufficient continuous evidence.")
    if shifts_expected is None:
        limitations.append("Whether shifting was expected is unknown.")
    if whole_run.get("timestamp_gap_count"):
        limitations.append(f"Recorded timestamps contain {whole_run['timestamp_gap_count']} gap(s); row coverage does not establish continuous time coverage.")
    insufficient = not whole_assessed
    if insufficient:
        summary = "Insufficient evidence for a complete gear assessment"
        if findings:
            summary += "; recorded findings still require review"
        status = "insufficient_evidence"
    elif findings:
        status = "review"
        summary = ("No gear variation observed; review run context" if all(item["scope"] == "whole_recording" for item in findings)
                   else "Localized findings to review")
    else:
        status, summary = "no_issues_detected", "No issues detected by completed checks"

    try:
        with Path(run["source"]).open("rb") as source_file:
            checksum = hashlib.file_digest(source_file, "sha256").hexdigest()
    except OSError:
        checksum = None
    distribution = [{"value": value, "samples": count, "share": count / statistics["numeric_samples"]}
                    for value, count in statistics.get("counts", {}).items()]
    coverage_count = _evidence_sample_count(findings)
    observation_intervals = (time_intervals(observations, timing) if timing["available"]
                             else observations.get("intervals", []))
    return {
        "schema_version": "1.1", "sensor": "Gear Position",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {"path": run["source"], "sha256": checksum,
                   "session": run["metadata"].get("Session"), "measurement_rows": total},
        "overall": {
            "status": status, "summary": summary,
            "assessment_scope": "insufficient" if insufficient else "limited",
            "finding_count": len(findings), "note_count": len(notes), "finding_evidence_samples": coverage_count,
            "finding_evidence_fraction": coverage_count / total if total else None,
            "coverage_note": "Evidence-window coverage of recorded rows; not sensor-health accuracy or proven fault duration.",
        },
        "timing": {"basis": timing.get("basis", "unavailable"),
                   "sample_rate_hz": timing.get("sample_rate_hz"), "reason": timing.get("reason")},
        "gear_mapping": {"reverse": -1, "neutral": 0, "forward": f"integer codes 1–{rules['maximum_forward_gear']}",
                         "maximum_forward_gear": rules["maximum_forward_gear"],
                         "maximum_forward_gear_status": "assumed", "source": "user_provided"},
        "analysis_settings": {"rules": copy.deepcopy(rules), "shifts_expected": shifts_expected},
        "data_summary": {
            "channel_available": statistics["available"], "total_samples": total,
            "numeric_samples": statistics.get("numeric_samples", 0),
            "missing_samples": statistics.get("missing_samples", 0),
            "invalid_samples": statistics.get("invalid_samples", 0),
            "fractional_samples": statistics.get("fractional_samples", 0),
            "outside_range_samples": quality["counts"].get("outside_range", 0),
            "distribution": distribution, "confirmed_gears": whole_run.get("confirmed_gears", []),
            "confirmed_reading_coverage": whole_run.get("confirmed_coverage"),
            "brief_unconfirmed_samples": whole_run.get("unconfirmed_samples", 0),
            "unresolved_samples": whole_run.get("unresolved_samples", 0),
            "raw_value_changes": statistics.get("raw_value_changes", 0),
        },
        "checks": checks, "findings": findings, "notes": notes, "limitations": limitations,
        "observations": {
            "intervals": observation_intervals,
            "data_quality_intervals": quality["intervals"],
            "brief_state_blocks": [copy.deepcopy(item) for item in states.get("intervals", []) if item["status"] == "unconfirmed"],
            "note": "Reverse intervals and brief readings are observations, not findings by themselves.",
        },
        "check_details": {"forward_sequence": transitions, "whole_run_no_shift": whole_run,
                          "gear_signal_quality": quality},
    }


def format_gear_report(report, detailed=False):
    overall, data = report["overall"], report["data_summary"]
    lines = ["\nGEAR SENSOR REPORT", f"File: {report['source']['path']}",
             f"Assessment: {overall['summary']}",
             f"Assessment scope: {overall['assessment_scope']} | Timing: {report['timing']['basis']}",
             f"Review findings: {overall['finding_count']}", f"Recorded samples: {data['total_samples']}",
             "Confirmed gears: " + (", ".join(gear_label(code) for code in data["confirmed_gears"]) or "none")]
    coverage = data["confirmed_reading_coverage"]
    lines.append(f"Confirmed reading coverage: {coverage:.2%}" if coverage is not None else "Confirmed reading coverage: unavailable")
    lines.append("Coverage measures repeated recorded readings, not sensor-health accuracy.")
    lines.append(f"Missing: {data['missing_samples']} | Invalid: {data['invalid_samples']} | Fractional: {data['fractional_samples']}")
    lines.append(f"Brief unconfirmed readings retained: {data['brief_unconfirmed_samples']}")
    lines.append(f"Informational transition notes: {len(report['notes'])}")
    lines += ["\nCHECKS", f"{'Check':<28} {'Outcome':<16} Assessment"]
    lines.extend(f"{check['name']:<28} {check['outcome']:<16} {check['assessment']}" for check in report["checks"])
    if report["findings"]:
        lines.append("\nFINDINGS")
    for finding in report["findings"]:
        location = finding["location"]
        lines += [f"{finding['id']} — {finding['title']} (review)",
                  f"  Samples {location['start_sample']}–{location['end_sample']}"]
        if location["start_seconds"] is not None:
            lines.append(f"  {location['time_basis']} time: {location['start_seconds']:.2f}–{location['end_seconds']:.2f} s; first-to-last evidence span {location['elapsed_span_seconds']:.2f} s")
        lines += [f"  {finding['message']}", f"  Next: {finding['suggested_action']}"]
    whole = report["check_details"]["whole_run_no_shift"]
    if whole["available"] and whole["assessment"] == "no_confirmed_changes" and not whole["findings"]:
        lines.append(f"\nInformation: {whole['message']}")
    lines.append("\nASSESSMENT LIMITATIONS")
    lines.extend(f"- {message}" for message in report["limitations"])
    if detailed:
        if report["notes"]:
            lines.append("\nTRANSITION NOTES")
            lines.extend(f"{item['id']}: {item['message']}" for item in report["notes"])
        lines.append("\nRECORDED VALUE DISTRIBUTION")
        lines.extend(f"{item['value']:g}: {item['samples']} samples ({item['share']:.2%})" for item in data["distribution"])
        lines.append("\nSETTINGS\n" + json.dumps(report["analysis_settings"], indent=2))
    return "\n".join(lines)
