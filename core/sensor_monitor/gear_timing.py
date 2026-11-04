"""Validate the time evidence used by duration and continuity checks."""

import math
from statistics import median

TOLERANCE = 1e-9


def inspect_timing(timing, total, maximum_gap_factor):
    result = {"available": False, "gap_after_sample": []}
    if not timing.get("available"):
        result["reason"] = timing.get("reason", "Usable timing is required for duration checks.")
        return result
    times = timing.get("seconds", [])
    if len(times) != total or total < 2:
        result["reason"] = "Timing must cover every measurement row and contain at least two timestamps."
        return result
    if not all(not isinstance(value, bool) and isinstance(value, (int, float))
               and math.isfinite(value) for value in times):
        result["reason"] = "Timestamps must be finite numbers."
        return result
    intervals = [end - start for start, end in zip(times, times[1:])]
    if any(value <= 0 for value in intervals):
        result["reason"] = "Timestamps must increase from row to row."
        return result
    maximum = median(intervals) * maximum_gap_factor
    return {"available": True, "seconds": times, "basis": timing["basis"],
            "maximum_gap_seconds": maximum,
            "gap_after_sample": [index for index, interval in enumerate(intervals)
                                 if interval > maximum + TOLERANCE]}
