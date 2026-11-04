"""Describe whole-recording gear variation without diagnosing sensor failure."""

import math
from statistics import median


def evaluate_no_shift_run(states, rules, *, shifts_expected=None, timing=None, run=None):
    """Review a single confirmed gear at EOF, subject to data-quality checks.

    Coverage is the fraction of recorded rows in confirmed gear blocks, not a
    claim about unrecorded driving time. Brief readings remain in the evidence.
    Unknown run purpose produces a provisional review; explicitly not expecting
    shifts produces information only. No elapsed-time threshold is applied.
    """
    if shifts_expected is not None and type(shifts_expected) is not bool:
        raise ValueError("shifts_expected must be True, False, or None.")

    result = {
        "available": False,
        "assessment": "unavailable",
        "summary": "Unavailable",
        "severity": "unassessed",
        "findings": [],
        "shifts_expected": shifts_expected,
        "time_basis": "sample_index",
        "timestamp_gap_count": None,
    }
    if not states["available"]:
        result["message"] = "Gear Position is unavailable."
        return result

    intervals = states["intervals"]
    total = sum(interval["sample_count"] for interval in intervals)
    if total == 0:
        result["message"] = "There are no measurement rows to assess."
        return result

    confirmed = [item for item in intervals if item["status"] == "confirmed"]
    gears = sorted({int(item["value"]) for item in confirmed})
    confirmed_samples = sum(item["sample_count"] for item in confirmed)
    minimum_coverage = rules["no_shift_minimum_confirmed_coverage"]
    coverage = confirmed_samples / total

    result.update({
        "available": True,
        "assessment": "insufficient_evidence",
        "summary": "Insufficient evidence",
        "total_samples": total,
        "confirmed_samples": confirmed_samples,
        "confirmed_coverage": coverage,
        "minimum_confirmed_coverage": minimum_coverage,
        "confirmed_gears": gears,
        "unconfirmed_samples": sum(
            item["sample_count"] for item in intervals if item["status"] == "unconfirmed"
        ),
        "unresolved_samples": sum(
            item["sample_count"] for item in intervals if item["status"] == "unresolved"
        ),
        "constant_recorded_value": (
            int(intervals[0]["value"])
            if len(intervals) == 1 and intervals[0]["status"] == "confirmed"
            else None
        ),
    })

    # A constant recorded series alone cannot establish continuity across gaps.
    if timing is not None and timing["available"]:
        times = timing["seconds"]
        if len(times) != total or len(times) < 2:
            result["message"] = "Timing does not cover every measurement row."
            return result
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in times):
            result["message"] = "Timestamps must be finite numbers."
            return result
        differences = [current - previous for previous, current in zip(times, times[1:])]
        if any(difference <= 0 for difference in differences):
            result["message"] = "Timestamps must increase from row to row."
            return result
        maximum_gap = median(differences) * rules["maximum_gap_factor"]
        result["timestamp_gap_count"] = sum(
            difference > maximum_gap + 1e-9 for difference in differences
        )
        result["time_basis"] = timing["basis"]

    if not gears:
        result["message"] = "No gear value met the confirmation requirement."
        return result

    if coverage + 1e-12 < minimum_coverage:
        result["message"] = (
            "Too few recorded rows belong to confirmed gear blocks to assess "
            "the whole-run no-change condition."
        )
        return result

    if len(gears) > 1:
        result["assessment"] = "multiple_gears_observed"
        result["summary"] = "Multiple confirmed gears observed"
        result["severity"] = "info"
        result["message"] = (
            "Multiple distinct gear values met confirmation; the whole-run "
            "no-change condition does not apply. Other checks remain independent."
        )
        return result

    if result["timestamp_gap_count"]:
        result["message"] = (
            "Only one gear was confirmed, but timestamp gaps prevent assessment "
            "across the whole recording."
        )
        return result

    gear = gears[0]
    description = {-1: "reverse (recorded gear -1)", 0: "neutral (recorded gear 0)"}.get(
        gear, f"gear {gear}",
    )
    if result["constant_recorded_value"] is not None:
        observation = f"{description.capitalize()} was recorded in every measurement row."
    else:
        observation = (
            f"Only {description} met confirmation; brief or unresolved readings "
            "were also recorded."
        )

    if shifts_expected is False:
        severity = "info"
        context = "This run was marked as not expecting gear changes."
    elif shifts_expected is True:
        severity = "review"
        context = "Gear changes were expected; review the recorded signal and run context."
    else:
        severity = "review"
        context = (
            "Whether shifting was expected is unknown; confirm the run purpose "
            "before treating this as a sensor issue."
        )

    gps = []
    if run is not None and "GPS Speed" in run["channels"]:
        for row in run["data"]:
            try:
                speed = float(row["GPS Speed"])
            except (TypeError, ValueError):
                continue
            if math.isfinite(speed):
                gps.append(speed)
    if gps:
        unit = run["units"].get("GPS Speed", "unit unspecified")
        result["gps_context"] = {"channel": "GPS Speed", "unit": unit, "minimum": min(gps),
                                 "median": median(gps), "maximum": max(gps), "numeric_samples": len(gps)}
        context += (f" Recorded GPS speed ranges from {min(gps):.2f} to {max(gps):.2f} {unit}. "
                    "GPS speed alone does not establish that shifting was required.")

    result["assessment"] = "no_confirmed_changes"
    result["summary"] = "No confirmed gear changes observed"
    result["severity"] = severity
    result["message"] = f"{observation} {context} This does not prove sensor failure."

    if severity == "review":
        result["findings"].append({
            "kind": result["summary"],
            "category": "run_observation",
            "severity": severity,
            "rule_version": rules["version"],
            "rule_status": rules["status"],
            "start_sample": 0,
            "end_sample": total - 1,
            "activation_sample": total - 1,
            "detected_at": "end_of_recording",
            "gear": gear,
            "confirmed_coverage": coverage,
            "shifts_expected": shifts_expected,
            "time_basis": result["time_basis"],
            "message": result["message"],
            "gps_context": result.get("gps_context"),
        })

    return result
