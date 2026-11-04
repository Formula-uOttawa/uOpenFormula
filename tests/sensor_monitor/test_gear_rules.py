import copy
import json
import unittest
from unittest.mock import mock_open, patch
from core.sensor_monitor.gear_rules import load_gear_rules


class GearRulesTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_gear_rules()
        self.rules["version"] = "test"

    def load(self, rules):
        with patch("core.sensor_monitor.gear_rules.Path.open", mock_open(read_data=json.dumps(rules))):
            return load_gear_rules()

    def test_valid_settings_do_not_need_reverse_duration_rule(self):
        self.assertEqual(self.load(self.rules), self.rules)
        self.assertNotIn("review_after_seconds", self.load(self.rules))

    def test_invalid_settings_are_rejected(self):
        cases = {"confirmation_samples": [True, 0, 1, 2.5],
                 "maximum_gap_factor": [True, 1, 0, float("nan"), float("inf"), "3"],
                 "no_shift_minimum_confirmed_coverage": [True, 0, 1.1, float("nan"), "0.9"],
                 "maximum_forward_gear": [True, 0, 6.5, "6"],
                 "large_jump_code_difference": [True, 0, 1, 2.5, "3"],
                 "large_jump_endpoint_seconds": [True, 0, -1, float("nan"), float("inf"), "0.5"],
                 "persistent_bad_seconds": [True, 0, -1, float("nan"), float("inf"), "1"]}
        for key, values in cases.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    rules = copy.deepcopy(self.rules)
                    rules[key] = value
                    with self.assertRaises(ValueError):
                        self.load(rules)


if __name__ == "__main__":
    unittest.main()
