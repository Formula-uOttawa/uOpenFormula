"""Presentation data shared by plots, independent of Dear PyGui."""

import math


def trace_segments(report, sensor):
    """Keep every numeric sample and split at invalid values or recorded gaps."""
    gaps = set(report["timing"]["gap_after_sample"])
    segments, x, y = [], [], []
    for index, (time, value) in enumerate(zip(report["timing"]["axis"], sensor["values"])):
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
    pool = [value for value in sensor["values"] if value is not None]
    if sensor["id"].startswith("brake_"):
        brakes = [item for item in report["sensors"]
                  if item["id"].startswith("brake_") and item["logged"]]
        if len(brakes) == 2 and all(item["unit"] == sensor["unit"] for item in brakes):
            pool = [value for item in brakes for value in item["values"] if value is not None] + [0]
    if not pool:
        return 0, 1
    low, high = min(pool), max(pool)
    pad = (1 if sensor["id"] == "gear" else max(abs(low) * .02, .01)) if low == high else (high - low) * .07
    return low - pad, high + pad


def finding_range(report, finding):
    last = len(report["timing"]["axis"]) - 1
    if finding["scope"] == "whole_recording":
        return 0, last
    location = finding["location"]
    pad = max(20, (location["end_sample"] - location["start_sample"]) * 2)
    return max(0, location["start_sample"] - pad), min(last, location["end_sample"] + pad)
