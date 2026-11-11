from collections import Counter
import math


def summarize_gear(run):
    if "Gear Position" not in run["channels"]:
        return {"available": False}

    counts = Counter()
    missing = 0
    invalid = 0
    fractional = 0
    changes = 0
    previous_value = None

    for row in run["data"]:
        raw_value = row["Gear Position"].strip()

        if raw_value == "":
            missing += 1
            previous_value = None
            continue

        try:
            value = float(raw_value)
        except ValueError:
            invalid += 1
            previous_value = None
            continue

        # Reject special numeric values such as NaN and infinity.
        if not math.isfinite(value):
            invalid += 1
            previous_value = None
            continue

        if previous_value is not None and value != previous_value:
            changes += 1
        previous_value = value
        counts[value] += 1

        if not value.is_integer():
            fractional += 1

    return {
        "available": True,
        "total_samples": len(run["data"]),
        "numeric_samples": sum(counts.values()),
        "missing_samples": missing,
        "invalid_samples": invalid,
        "fractional_samples": fractional,
        "raw_value_changes": changes,
        "counts": dict(sorted(counts.items())),
    }


def find_gear_observation_intervals(run):
    if "Gear Position" not in run["channels"]:
        return {"available": False}

    intervals = []
    current = None

    for sample_index, row in enumerate(run["data"]):
        try:
            value = float(row["Gear Position"])
        except ValueError:
            value = math.nan

        # Classify the observation without diagnosing a fault.
        if not math.isfinite(value):
            kind = None
        elif value == -1:
            kind = "Reverse gear (-1)"
        elif not value.is_integer():
            kind = "Fractional readings"
        else:
            kind = None

        # End the interval when its observation type changes.
        if current is not None and kind != current["kind"]:
            intervals.append(current)
            current = None

        if kind is None:
            continue

        # Start a new interval.
        if current is None:
            current = {
                "kind": kind,
                "start_sample": sample_index,
                "end_sample": sample_index,
                "sample_count": 1,
                "values": [value],
            }

        # Extend an existing interval of the same type.
        else:
            current["end_sample"] = sample_index
            current["sample_count"] += 1

            if value not in current["values"]:
                current["values"].append(value)

    # Keep an interval that continues to the end of the file.
    if current is not None:
        intervals.append(current)

    return {
        "available": True,
        "intervals": intervals,
    }
