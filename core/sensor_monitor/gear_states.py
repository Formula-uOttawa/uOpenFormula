import math
from itertools import groupby


def _classify_gear(raw_value, maximum_forward_gear=6):
    text = "" if raw_value is None else str(raw_value).strip()

    if text == "":
        return "missing", None

    try:
        value = float(text)
    except ValueError:
        return "invalid", None

    if not math.isfinite(value):
        return "invalid", None

    # -1 is reverse and 0 is neutral, using the user-provided mapping.
    if -1 <= value <= maximum_forward_gear and value.is_integer():
        return "whole-number", value

    return "unresolved", value


def build_gear_states(run, confirmation_samples=3, maximum_forward_gear=6):
    """Group readings and confirm repetition by sample count only."""
    if type(confirmation_samples) is not int or confirmation_samples < 2:
        raise ValueError("confirmation_samples must be an integer of at least 2.")
    if type(maximum_forward_gear) is not int or maximum_forward_gear < 1:
        raise ValueError("maximum_forward_gear must be a positive integer.")

    if "Gear Position" not in run["channels"]:
        return {"available": False, "intervals": []}

    intervals = []

    groups = groupby(
        enumerate(run["data"]),
        key=lambda item: _classify_gear(item[1]["Gear Position"], maximum_forward_gear),
    )

    for (kind, value), group in groups:
        indices = [index for index, row in group]
        count = len(indices)

        if kind != "whole-number":
            status = "unresolved"
        elif count >= confirmation_samples:
            status = "confirmed"
        else:
            status = "unconfirmed"

        intervals.append({
            "kind": kind,
            "value": value,
            "start_sample": indices[0],
            "end_sample": indices[-1],
            "sample_count": count,
            "status": status,
            "confirmation_sample": (
                indices[confirmation_samples - 1]
                if status == "confirmed" else None
            ),
        })

    return {
        "available": True,
        "confirmation_samples": confirmation_samples,
        "confirmation_basis": "sample_count",
        "maximum_forward_gear": maximum_forward_gear,
        "intervals": intervals,
    }
