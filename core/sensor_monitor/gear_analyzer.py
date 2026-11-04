from collections import Counter
import math


def summarize_gear(run):
    if "Gear Position" not in run["channels"]:
        return {"available": False}

    counts = Counter()
    missing = 0
    invalid = 0
    fractional = 0

    for row in run["data"]:
        raw_value = row["Gear Position"].strip()

        if raw_value == "":
            missing += 1
            continue

        try:
            value = float(raw_value)
        except ValueError:
            invalid += 1
            continue

        # Reject special numeric values such as NaN and infinity.
        if not math.isfinite(value):
            invalid += 1
            continue

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
        "counts": dict(sorted(counts.items())),
    }

def inspect_gear_sequence(run):
    if "Gear Position" not in run["channels"]:
        return {"available": False}

    changes = []
    fractional_readings = []

    previous_value = None
    previous_index = None

    for sample_index, row in enumerate(run["data"]):
        try:
            value = float(row["Gear Position"])
        except ValueError:
            previous_value = None
            previous_index = None
            continue

        if not math.isfinite(value):
            previous_value = None
            previous_index = None
            continue

        if not value.is_integer():
            fractional_readings.append({
                "sample_index": sample_index,
                "value": value,
            })

        if previous_value is not None and value != previous_value:
            changes.append({
                "from_sample": previous_index,
                "to_sample": sample_index,
                "from_value": previous_value,
                "to_value": value,
            })

        previous_value = value
        previous_index = sample_index

    return {
        "available": True,
        "changes": changes,
        "fractional_readings": fractional_readings,
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
