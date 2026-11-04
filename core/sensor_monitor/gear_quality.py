"""Find persistent unusable gear data without rounding or replacing readings."""

from collections import Counter

from .gear_states import _classify_gear
from .gear_timing import inspect_timing, TOLERANCE

TITLES = {"fractional": "Persistent fractional gear readings",
          "outside_range": "Persistent out-of-range gear readings",
          "missing": "Persistent missing gear readings",
          "invalid": "Persistent invalid gear readings"}


def evaluate_gear_quality(run, timing, rules):
    result = {"available": False, "findings": [], "intervals": [], "counts": {}}
    if "Gear Position" not in run["channels"]:
        result["reason"] = "Gear Position is unavailable."
        return result
    maximum = rules["maximum_forward_gear"]
    categories = []
    raw = [row["Gear Position"] for row in run["data"]]
    for value in raw:
        kind, number = _classify_gear(value, maximum)
        categories.append(None if kind == "whole-number" else kind if kind in ("missing", "invalid")
                          else "outside_range" if number < -1 or number > maximum else "fractional")
    counts = Counter(category for category in categories if category is not None)
    result["counts"] = {kind: counts[kind] for kind in TITLES}
    clock = inspect_timing(timing, len(raw), rules["maximum_gap_factor"])
    result.update({"available": clock["available"], "threshold_seconds": rules["persistent_bad_seconds"],
                   "time_basis": clock.get("basis", "unavailable"),
                   "timestamp_gap_count": len(clock["gap_after_sample"])})
    if not clock["available"]:
        result["reason"] = clock["reason"]
    gaps = set(clock["gap_after_sample"])
    times = clock.get("seconds", [])
    # Group by unusable status, not exact value or category. A continuous mix of
    # fractions, out-of-range numbers and blanks should produce one episode.
    start = None
    ranges = []
    for index, category in enumerate(categories):
        if start is not None and (category is None or index - 1 in gaps):
            ranges.append((start, index - 1))
            start = None
        if category is not None and start is None:
            start = index
    if start is not None:
        ranges.append((start, len(raw) - 1))
    for start, end in ranges:
        observed = Counter(categories[start:end + 1])
        span = times[end] - times[start] if clock["available"] else None
        activation = (next((index for index in range(start, end + 1)
                            if times[index] - times[start] + TOLERANCE >= rules["persistent_bad_seconds"]), None)
                      if clock["available"] else None)
        item = {"kind": TITLES[next(iter(observed))] if len(observed) == 1 else "Persistent unusable gear readings",
                "start_sample": start, "end_sample": end, "sample_count": end - start + 1,
                "activation_sample": activation, "elapsed_span_seconds": span,
                "category_counts": dict(observed), "example_values": list(dict.fromkeys(raw[start:end + 1]))[:12],
                "continues_at_file_end": end == len(raw) - 1,
                "time_basis": result["time_basis"], "threshold_seconds": rules["persistent_bad_seconds"]}
        result["intervals"].append(item)
        if activation is None:
            continue
        description = ", ".join(f"{name.replace('_', ' ')}: {count}" for name, count in observed.items())
        examples = ", ".join(str(value)[:24] if str(value).strip() else "(blank)" for value in item["example_values"][:3])
        item.update({"severity": "review", "rule_version": rules["version"], "rule_status": rules["status"],
                     "category": "signal_data",
                     "message": f"Unusable gear readings span {span:.2f} s ({description}). "
                                f"Examples: {examples}. "
                                f"The provisional threshold is {rules['persistent_bad_seconds']:g} s.",
                     "suggested_action": "Inspect the recorded values, sensor wiring, channel calibration and export settings."})
        result["findings"].append(item.copy())
    result["message"] = (f"{len(result['findings'])} persistent unusable-data episode(s); "
                         "brief episodes are retained as observations.") if clock["available"] else result["reason"]
    return result
