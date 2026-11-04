import json
import math
from pathlib import Path


def load_gear_rules():
    path = Path(__file__).with_name("gear_rules.json")

    with path.open("r", encoding="utf-8") as file:
        rules = json.load(file)

    factor = rules["maximum_gap_factor"]
    if (
        isinstance(factor, bool) or not isinstance(factor, (int, float))
        or not math.isfinite(factor) or factor <= 1
    ):
        raise ValueError("maximum_gap_factor must be finite and greater than 1.")

    samples = rules["confirmation_samples"]
    if type(samples) is not int or samples < 2:
        raise ValueError("confirmation_samples must be an integer of at least 2.")

    coverage = rules["no_shift_minimum_confirmed_coverage"]
    if (
        isinstance(coverage, bool)
        or not isinstance(coverage, (int, float))
        or not math.isfinite(coverage)
        or not 0 < coverage <= 1
    ):
        raise ValueError("no_shift_minimum_confirmed_coverage must be greater than 0 and at most 1.")

    for name, minimum in (("maximum_forward_gear", 1), ("large_jump_code_difference", 2)):
        value = rules[name]
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer of at least {minimum}.")
    for name in ("large_jump_endpoint_seconds", "persistent_bad_seconds"):
        value = rules[name]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0):
            raise ValueError(f"{name} must be positive and finite.")

    return rules
