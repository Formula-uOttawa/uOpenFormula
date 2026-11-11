"""Provisional checks for throttle position and the two ECU temperatures."""

from collections import deque
from itertools import groupby

from .gear_timing import TOLERANCE


THROTTLE_LOW = -1.0
THROTTLE_HIGH = 101.0
THROTTLE_HOLD_SECONDS = 0.25
TEMPERATURE_RISE_C = 5.0
TEMPERATURE_WINDOW_SECONDS = 0.5

SCREENED_SENSORS = {"throttle", "iat", "coolant"}


def _valid_blocks(values, gap_after):
    start = 0
    for index, value in enumerate(values):
        if index - 1 in gap_after:
            if start < index:
                yield range(start, index)
            start = index
        if value is None:
            if start < index:
                yield range(start, index)
            start = index + 1
    if start < len(values):
        yield range(start, len(values))


def _throttle_events(values, times, blocks):
    assessed = False
    events = []
    for block in blocks:
        if times[block[-1]] - times[block[0]] < THROTTLE_HOLD_SECONDS - TOLERANCE:
            continue
        assessed = True
        groups = groupby(block, key=lambda i: not THROTTLE_LOW <= values[i] <= THROTTLE_HIGH)
        for outside, indices in groups:
            if not outside:
                continue
            start = end = next(indices)
            activation = None
            for end in indices:
                if activation is None and times[end] - times[start] >= THROTTLE_HOLD_SECONDS - TOLERANCE:
                    activation = end
            if activation is not None:
                elapsed = times[end] - times[start]
                events.append((start, end, activation,
                               f"Throttle stayed outside {THROTTLE_LOW:g}% to {THROTTLE_HIGH:g}% "
                               f"for {elapsed:.3g} s of readings."))
    return assessed, events


def _temperature_events(values, times, blocks):
    assessed = False
    events = []
    for block in blocks:
        baselines = deque()
        active = False
        for end in block:
            # Keep the lowest earlier reading still inside the window at the front.
            while baselines and times[end] - times[baselines[0]] > TEMPERATURE_WINDOW_SECONDS + TOLERANCE:
                baselines.popleft()
            rise = 0.0
            if baselines:
                assessed = True
                start = baselines[0]
                rise = values[end] - values[start]
            if rise > TEMPERATURE_RISE_C + TOLERANCE:
                if not active:
                    elapsed = times[end] - times[start]
                    events.append((start, end, end, f"Temperature rose from {values[start]:g} °C "
                                   f"to {values[end]:g} °C in {elapsed:.3g} s."))
                active = True
            else:
                active = False
            while baselines and values[baselines[-1]] >= values[end]:
                baselines.pop()
            baselines.append(end)
    return assessed, events


def _finding(sensor, run, timing, check, number, event):
    start, end, activation, message = event
    times = timing["seconds"]
    indices = sorted({start, activation, end})
    return {
        "id": f"{sensor['id'].upper()}-{number:03d}",
        "check_id": check["id"], "severity": "review", "category": "signal_screening",
        "scope": "local_event", "title": check["name"], "message": message,
        "location": {"start_sample": start, "end_sample": end, "activation_sample": activation,
                     "time_basis": timing["basis"], "start_seconds": times[start],
                     "end_seconds": times[end], "elapsed_span_seconds": times[end] - times[start]},
        "rule_version": "1.0", "rule_status": "provisional",
        "evidence": {"sample_window": [{"sample_index": i, "seconds": times[i],
                                        "raw_value": run["data"][i][sensor["channel"]]} for i in indices]},
        "suggested_action": "Inspect the trace around the marked readings.",
    }


def evaluate_screening(sensor, run, timing, gap_after):
    throttle = sensor["id"] == "throttle"
    unit = "%" if throttle else "°C"
    criterion = (f"Review readings below {THROTTLE_LOW:g}% or above {THROTTLE_HIGH:g}% "
                 f"for at least {THROTTLE_HOLD_SECONDS:g} s." if throttle else
                 f"Review a rise greater than {TEMPERATURE_RISE_C:g} °C within "
                 f"{TEMPERATURE_WINDOW_SECONDS:g} s.")
    check = {
        "id": "throttle_screening_band" if throttle else "abrupt_temperature_rise",
        "name": "Throttle outside screening band" if throttle else "Abrupt temperature rise",
        "criterion": criterion,
        "assessment": "unavailable", "outcome": "unassessed", "finding_count": 0,
    }
    sensor["checks"] = [check]
    if sensor["id"] == "coolant":
        sensor["limitations"].append("Coolant operating warnings require team-approved temperature limits.")
    if sensor["unit"].strip() != unit:
        actual_unit = sensor["unit"].strip() or "unavailable"
        reason = f"This check requires {unit}. CSV unit: {actual_unit}."
    elif not sensor["data_summary"]["numeric_samples"]:
        reason = "This check needs usable numeric readings."
    elif not timing["available"]:
        reason = "This check needs usable timing. " + timing["reason"]
    else:
        reason = None

    if reason is None:
        values, times = sensor["values"], timing["seconds"]
        blocks = list(_valid_blocks(values, set(gap_after)))
        evaluate = _throttle_events if throttle else _temperature_events
        assessed, events = evaluate(values, times, blocks)
        if assessed:
            partial = len(blocks) != 1 or len(blocks[0]) != len(values)
            sensor["findings"] = [_finding(sensor, run, timing, check, number, event)
                                  for number, event in enumerate(events, 1)]
            check.update({
                "assessment": "partial" if partial else "complete",
                "outcome": "review" if events else "not_triggered", "finding_count": len(events),
                "message": criterion,
            })
            if partial:
                sensor["limitations"].append("The check skips missing or invalid readings and starts over after timestamp gaps.")
            scope = "Partial trial screening" if partial else "Trial screening"
            if events:
                return "review", f"{check['name']} ({len(events)}).", scope
            observation = ("No sustained throttle excursions outside the screening band." if throttle else
                           "No abrupt rises in the usable temperature readings.")
            return "no_findings", observation, scope
        reason = (f"Needs at least {THROTTLE_HOLD_SECONDS:g} s of continuous usable readings." if throttle else
                  f"Needs two continuous usable readings within {TEMPERATURE_WINDOW_SECONDS:g} s.")

    check["message"] = reason
    return "not_assessed", reason, "Trial screening unavailable"
