"""Presentation data shared by plots, independent of Dear PyGui."""

import math


def trace_segments(report, sensor):
    """Return plot coordinates for reading only, splitting at invalid values or gaps."""
    timing = report["timing"]
    axis, values = timing["axis"], sensor["values"]
    gaps = set(timing["gap_after_sample"])
    summary = sensor.get("data_summary")
    if not gaps and summary and axis and summary["numeric_samples"] == len(values) == len(axis):
        return [(axis, values)]

    segments, x, y = [], [], []
    for index, (time, value) in enumerate(zip(axis, values)):
        valid = value is not None and math.isfinite(value) and math.isfinite(time)
        if not valid or index - 1 in gaps:
            if x:
                segments.append((x, y))
            x, y = [], []
        if valid:
            x.append(time)
            y.append(value)
    if x:
        segments.append((x, y))
    return segments


def value_limits(report, sensor):
    """Match the HTML report's scale, including paired brake pressure scales."""
    summary = sensor["data_summary"]
    low, high = (summary["minimum"], summary["maximum"]) if summary else (None, None)
    if sensor["id"].startswith("brake_"):
        brakes = [item for item in report["sensors"]
                  if item["id"].startswith("brake_") and item["logged"]]
        if len(brakes) == 2 and all(item["unit"] == sensor["unit"] for item in brakes):
            summaries = [item["data_summary"] for item in brakes if item["data_summary"]["numeric_samples"]]
            low = min([0, *(data["minimum"] for data in summaries)])
            high = max([0, *(data["maximum"] for data in summaries)])
    if low is None:
        return 0, 1
    pad = (1 if sensor["id"] == "gear" else max(abs(low) * .02, .01)) if low == high else (high - low) * .07
    return low - pad, high + pad


def finding_range(report, finding):
    last = len(report["timing"]["axis"]) - 1
    if finding["scope"] == "whole_recording":
        return 0, last
    location = finding["location"]
    pad = max(20, (location["end_sample"] - location["start_sample"]) * 2)
    return max(0, location["start_sample"] - pad), min(last, location["end_sample"] + pad)
