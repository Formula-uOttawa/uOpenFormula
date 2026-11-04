"""Review large recorded changes; preserve intermediate states and small notes."""

from .gear_timing import inspect_timing, TOLERANCE


def _has_brief_sequential_path(start, end, observations):
    step = 1 if end > start else -1
    expected = start + step
    for observation in observations:
        if observation["kind"] == "whole-number" and observation["value"] == expected:
            expected += step
            if expected == end:
                return True
    return False


def _longest_unresolved_span(intervals, times):
    first, previous_end, longest = None, None, 0.0
    for item in intervals:
        if item["kind"] == "whole-number":
            first = None
        else:
            if first is None or previous_end != item["start_sample"] - 1:
                first = item["start_sample"]
            longest = max(longest, times[item["end_sample"]] - times[first])
        previous_end = item["end_sample"]
    return longest


def evaluate_gear_transitions(states, timing, rules):
    result = {"available": False, "transitions": [], "findings": [], "notes": [],
              "unassessed": [], "neutral_not_checked": [], "reverse_not_checked": []}
    if not states["available"]:
        result["reason"] = "Gear Position is unavailable."
        return result
    intervals = states["intervals"]
    total = intervals[-1]["end_sample"] + 1 if intervals else 0
    clock = inspect_timing(timing, total, rules["maximum_gap_factor"])
    if not clock["available"]:
        result["reason"] = clock["reason"]
        return result
    times, gaps = clock["seconds"], clock["gap_after_sample"]
    hold = rules["large_jump_endpoint_seconds"]
    minimum_jump = rules["large_jump_code_difference"]
    maximum = rules["maximum_forward_gear"]
    result.update({"available": True, "time_basis": clock["basis"],
                   "maximum_gap_seconds": clock["maximum_gap_seconds"],
                   "minimum_code_difference": minimum_jump, "endpoint_seconds": hold})
    # Keep all basically confirmed states. Increasing the review window must
    # never remove an intermediate confirmed state and invent a new jump.
    confirmed = [(index, item) for index, item in enumerate(intervals) if item["status"] == "confirmed"]
    for (left_index, left), (right_index, right) in zip(confirmed, confirmed[1:]):
        between = intervals[left_index + 1:right_index]
        start, end = int(left["value"]), int(right["value"])
        source_first = max([left["start_sample"]] + [gap + 1 for gap in gaps
                            if left["start_sample"] <= gap < left["end_sample"]])
        destination_last = min([right["end_sample"]] + [gap for gap in gaps
                               if right["start_sample"] <= gap < right["end_sample"]])
        source_span = times[left["end_sample"]] - times[source_first]
        destination_span = times[destination_last] - times[right["start_sample"]]
        activation = next((index for index in range(right["start_sample"], destination_last + 1)
                           if times[index] - times[right["start_sample"]] + TOLERANCE >= hold), None)
        base_window = left["end_sample"] - states["confirmation_samples"] + 1
        has_gap = any(base_window <= gap < right["confirmation_sample"] for gap in gaps)
        unusable = any(item["kind"] in ("missing", "invalid") or (
            item["kind"] == "unresolved" and (item["value"] < -1 or item["value"] > maximum))
                       for item in between)
        long_unresolved = _longest_unresolved_span(between, times) + TOLERANCE >= rules["persistent_bad_seconds"]
        transition = {
            "from_gear": start, "to_gear": end, "code_difference": abs(end - start),
            "start_sample": left["end_sample"], "end_sample": right["start_sample"],
            "activation_sample": right["confirmation_sample"],
            "activation_seconds": times[right["confirmation_sample"]], "time_basis": clock["basis"],
            "source_span_seconds": source_span, "destination_span_seconds": destination_span,
            "endpoint_threshold_seconds": hold, "minimum_code_difference": minimum_jump,
            "intermediate_observations": [item.copy() for item in between],
        }
        if has_gap:
            assessment, reason = "unassessed", "A timestamp gap interrupts the transition or basic endpoint confirmation."
        elif unusable or long_unresolved:
            assessment, reason = "unassessed", "Unusable or persistent unresolved readings interrupt this comparison; inspect the data-quality assessment."
        elif start == end:
            assessment, reason = "same_endpoints", "The confirmed endpoint readings show the same gear."
        elif start == -1 or end == -1:
            assessment, reason = "reverse_not_checked", "Reverse is a valid code; numerical forward-gear jump distance does not apply."
        elif abs(end - start) == 1:
            assessment, reason = "adjacent_endpoints", "The confirmed codes are adjacent."
        elif _has_brief_sequential_path(start, end, between):
            assessment, reason = "brief_intermediate_evidence", "Brief intermediate readings provide an ordered path."
        elif abs(end - start) < minimum_jump:
            assessment, reason = "smaller_skip_note", f"Recorded change {start} to {end} is below the {minimum_jump}-code review threshold."
        elif source_span + TOLERANCE < hold or destination_span + TOLERANCE < hold:
            interrupted_hold = (source_first != left["start_sample"] or destination_last != right["end_sample"])
            assessment = "unassessed" if interrupted_hold else "brief_endpoint_observation"
            reason = ("A timestamp gap prevents endpoint persistence confirmation." if interrupted_hold
                      else f"Both endpoints did not persist for {hold:g} s; retain as a brief observation.")
        else:
            assessment = "large_change"
            reason = (f"Recorded change {start} to {end} has a code difference of {abs(end - start)}. "
                      f"Both endpoint plateaus persist for at least {hold:g} s. "
                      "This is a review of the recorded pattern, not proof of sensor failure.")
            transition.update({"activation_sample": activation, "activation_seconds": times[activation],
                               "kind": f"Large recorded gear change: {start} to {end}", "category": "transition_pattern",
                               "severity": "review", "rule_version": rules["version"], "rule_status": rules["status"]})
        transition.update({"assessment": assessment, "reason": reason})
        result["transitions"].append(transition)
        if assessment == "large_change":
            result["findings"].append(transition)
        elif assessment == "unassessed":
            result["unassessed"].append(transition)
        elif assessment == "reverse_not_checked":
            result["reverse_not_checked"].append(transition)
        elif assessment in ("smaller_skip_note", "brief_endpoint_observation"):
            result["notes"].append(transition)
    return result
