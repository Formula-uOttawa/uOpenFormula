import math


def build_timing(run, allow_estimated=False):
    rows = run["data"]

    if not rows:
        raise ValueError("There are no measurement rows to time.")

    if run["units"].get("Time", "").strip() != "s":
        raise ValueError("This timing module requires Time units of seconds.")

    raw_times = [row["Time"].strip() for row in rows]

    # Use recorded timestamps when they are complete and usable.
    if any(raw_times):
        if not all(raw_times):
            raise ValueError("Timestamps are partially missing.")

        try:
            seconds = [float(value) for value in raw_times]
        except ValueError:
            raise ValueError("Some timestamps are not numeric.") from None

        if not all(math.isfinite(value) for value in seconds):
            raise ValueError("Some timestamps are not finite numbers.")

        if any(
            current <= previous
            for previous, current in zip(seconds, seconds[1:])
        ):
            raise ValueError("Timestamps must increase from row to row.")

        return {
            "available": True,
            "basis": "recorded",
            "seconds": seconds,
        }

    # All timestamps are blank. Estimation requires user opt-in.
    if not allow_estimated:
        return {
            "available": False,
            "reason": "All recorded timestamps are blank.",
        }

    try:
        rate = float(run["metadata"]["Sample Rate"])
        duration = float(run["metadata"]["Duration"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(
            "Estimation requires numeric Sample Rate and Duration metadata."
        ) from None

    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("The sample rate must be positive and finite.")

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("The declared duration must be positive and finite.")

    # Check that the metadata supports this estimate.
    if abs(len(rows) / rate - duration) > 1 / rate + 1e-9:
        raise ValueError(
            "Row count, sample rate and declared duration do not agree."
        )

    return {
        "available": True,
        "basis": "estimated",
        "seconds": [index / rate for index in range(len(rows))],
        "sample_rate_hz": rate,
    }


def time_intervals(observations, timing):
    timed_intervals = []

    if not timing["available"]:
        return timed_intervals

    for interval in observations["intervals"]:
        timed = interval.copy()

        start = timing["seconds"][interval["start_sample"]]
        end = timing["seconds"][interval["end_sample"]]

        timed["time_basis"] = timing["basis"]
        timed["start_seconds"] = start
        timed["end_seconds"] = end
        timed["elapsed_span_seconds"] = end - start

        timed_intervals.append(timed)

    return timed_intervals