import copy
import json
import unittest
from unittest.mock import mock_open, patch

from core.sensor_monitor.gear_rules import load_gear_rules
from core.sensor_monitor.gear_run import evaluate_no_shift_run
from core.sensor_monitor.gear_states import build_gear_states


def make_states(values):
    return build_gear_states({
        "channels": ["Gear Position"],
        "data": [{"Gear Position": str(value)} for value in values],
    })


class WholeRunGearTests(unittest.TestCase):
    def setUp(self):
        self.rules = {
            "version": "test", "status": "provisional",
            "maximum_gap_factor": 3.0,
            "no_shift_minimum_confirmed_coverage": 0.9,
        }

    def review(self, values, shifts_expected=None, timing=None):
        return evaluate_no_shift_run(
            make_states(values), self.rules,
            shifts_expected=shifts_expected, timing=timing,
        )

    def test_constant_neutral_in_expected_shifting_run_is_reviewed_at_eof(self):
        result = self.review([0] * 20, shifts_expected=True)
        self.assertEqual(result["assessment"], "no_confirmed_changes")
        self.assertEqual(result["confirmed_gears"], [0])
        self.assertEqual(result["constant_recorded_value"], 0)
        self.assertEqual(result["confirmed_coverage"], 1.0)
        self.assertEqual(len(result["findings"]), 1)
        finding = result["findings"][0]
        self.assertEqual(finding["activation_sample"], 19)
        self.assertEqual(finding["detected_at"], "end_of_recording")
        self.assertIn("neutral", finding["message"].lower())
        self.assertIn("does not prove sensor failure", finding["message"])

    def test_constant_forward_gear_is_also_reviewed(self):
        result = self.review([3] * 20, shifts_expected=True)
        self.assertEqual(result["confirmed_gears"], [3])
        self.assertEqual(len(result["findings"]), 1)

    def test_stationary_or_single_gear_test_is_informational(self):
        for gear in (0, 3):
            with self.subTest(gear=gear):
                result = self.review([gear] * 20, shifts_expected=False)
                self.assertEqual(result["assessment"], "no_confirmed_changes")
                self.assertEqual(result["severity"], "info")
                self.assertEqual(result["findings"], [])
                self.assertIn("not expecting gear changes", result["message"])

    def test_unknown_run_purpose_is_explicitly_qualified(self):
        result = self.review([0] * 20)
        self.assertEqual(result["severity"], "review")
        self.assertIsNone(result["shifts_expected"])
        self.assertIn("expected is unknown", result["message"])

    def test_multiple_confirmed_gears_do_not_trigger_no_shift_rule(self):
        result = self.review([0] * 10 + [1] * 10 + [2] * 10)
        self.assertEqual(result["assessment"], "multiple_gears_observed")
        self.assertEqual(result["findings"], [])

    def test_brief_whole_number_spike_does_not_hide_constant_confirmed_gear(self):
        result = self.review([0] * 10 + [2] + [0] * 10)
        self.assertEqual(result["assessment"], "no_confirmed_changes")
        self.assertEqual(result["confirmed_gears"], [0])
        self.assertEqual(result["unconfirmed_samples"], 1)
        self.assertIsNone(result["constant_recorded_value"])
        self.assertIn("Only neutral", result["message"])
        self.assertNotIn("every measurement row", result["message"])

    def test_small_unresolved_subset_is_counted_without_claiming_all_values_equal(self):
        for value in (-2, 0.2, "", "bad"):
            with self.subTest(value=value):
                result = self.review([0] * 10 + [value] + [0] * 10)
                self.assertEqual(result["assessment"], "no_confirmed_changes")
                self.assertEqual(result["unresolved_samples"], 1)
                self.assertIsNone(result["constant_recorded_value"])

    def test_low_coverage_is_unassessed_instead_of_stuck_sensor_finding(self):
        result = self.review([0] * 10 + [""] * 10)
        self.assertEqual(result["confirmed_coverage"], 0.5)
        self.assertEqual(result["assessment"], "insufficient_evidence")
        self.assertEqual(result["severity"], "unassessed")
        self.assertEqual(result["findings"], [])

    def test_all_unresolved_or_all_unconfirmed_has_insufficient_evidence(self):
        for values in ([-2] * 20, [0, 1] * 10, [0, 0]):
            with self.subTest(values=values):
                result = self.review(values)
                self.assertEqual(result["assessment"], "insufficient_evidence")
                self.assertEqual(result["findings"], [])

    def test_exact_coverage_boundary_qualifies(self):
        result = self.review([0] * 9 + [1])
        self.assertAlmostEqual(result["confirmed_coverage"], 0.9)
        self.assertEqual(result["assessment"], "no_confirmed_changes")
        self.assertEqual(len(result["findings"]), 1)

    def test_below_coverage_boundary_does_not_qualify(self):
        result = self.review([0] * 8 + [1])
        self.assertEqual(result["assessment"], "insufficient_evidence")
        self.assertEqual(result["findings"], [])

    def test_coverage_requirement_is_configurable(self):
        self.rules["no_shift_minimum_confirmed_coverage"] = 1.0
        result = self.review([0] * 10 + [1] + [0] * 10)
        self.assertEqual(result["assessment"], "insufficient_evidence")

    def test_missing_channel_and_empty_recording_are_unavailable(self):
        self.assertFalse(evaluate_no_shift_run(
            {"available": False, "intervals": []}, self.rules,
        )["available"])
        self.assertFalse(self.review([])["available"])

    def test_timestamp_gap_prevents_whole_run_no_change_finding(self):
        times = [index / 20 + (1 if index >= 10 else 0) for index in range(20)]
        result = self.review(
            [0] * 20,
            timing={"available": True, "basis": "recorded", "seconds": times},
        )
        self.assertEqual(result["timestamp_gap_count"], 1)
        self.assertEqual(result["assessment"], "insufficient_evidence")
        self.assertEqual(result["findings"], [])

    def test_declining_timing_still_allows_qualified_row_based_observation(self):
        result = self.review([0] * 20, timing={"available": False})
        self.assertEqual(result["time_basis"], "sample_index")
        self.assertIsNone(result["timestamp_gap_count"])
        self.assertEqual(len(result["findings"]), 1)

    def test_bad_timing_is_unassessed(self):
        for times in ([0, 0.05], [0, 0, 0], [0, float("nan"), 0.1]):
            with self.subTest(times=times):
                result = self.review(
                    [0] * 3,
                    timing={"available": True, "basis": "recorded", "seconds": times},
                )
                self.assertEqual(result["assessment"], "insufficient_evidence")
                self.assertEqual(result["findings"], [])

    def test_estimated_timing_remains_labelled(self):
        result = self.review(
            [0] * 20,
            timing={
                "available": True, "basis": "estimated",
                "seconds": [index / 20 for index in range(20)],
            },
        )
        self.assertEqual(result["findings"][0]["time_basis"], "estimated")

    def test_run_expectation_must_be_explicit_boolean_or_unknown(self):
        for expectation in (0, 1, "yes"):
            with self.subTest(expectation=expectation), self.assertRaises(ValueError):
                self.review([0] * 20, shifts_expected=expectation)

    def test_input_evidence_and_settings_are_unchanged(self):
        states = make_states([0] * 10 + [2] + [0] * 10)
        original = copy.deepcopy(states)
        original_rules = copy.deepcopy(self.rules)
        evaluate_no_shift_run(states, self.rules)
        self.assertEqual(states, original)
        self.assertEqual(self.rules, original_rules)


class WholeRunConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_gear_rules()
        self.rules["version"] = "test"

    def test_valid_coverage_setting_loads(self):
        with patch("core.sensor_monitor.gear_rules.Path.open", mock_open(read_data=json.dumps(self.rules))):
            self.assertEqual(load_gear_rules()["no_shift_minimum_confirmed_coverage"], 0.9)

    def test_invalid_coverage_settings_are_rejected(self):
        for value in (True, 0, -0.1, 1.1, "0.9", float("nan"), float("inf")):
            with self.subTest(value=value):
                self.rules["no_shift_minimum_confirmed_coverage"] = value
                with patch("core.sensor_monitor.gear_rules.Path.open", mock_open(read_data=json.dumps(self.rules))):
                    with self.assertRaises(ValueError):
                        load_gear_rules()


if __name__ == "__main__":
    unittest.main()
