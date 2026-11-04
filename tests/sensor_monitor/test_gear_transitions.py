import copy
import unittest

from core.sensor_monitor.gear_states import build_gear_states
from core.sensor_monitor.gear_transitions import evaluate_gear_transitions
from core.sensor_monitor.gear_rules import load_gear_rules


def make_states(values):
    return build_gear_states({
        "channels": ["Gear Position"],
        "data": [{"Gear Position": str(value)} for value in values],
    })


class GearTransitionTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_gear_rules()
        self.rules["version"] = "test"

    def review(self, values, times=None, basis="recorded"):
        if times is None:
            times = [index / 20 for index in range(len(values))]
        return evaluate_gear_transitions(
            make_states(values),
            {"available": True, "basis": basis, "seconds": times},
            self.rules,
        )

    def test_adjacent_upshifts_and_downshifts_have_no_findings(self):
        values = [1] * 3 + [2] * 3 + [3] * 3 + [2] * 3 + [1] * 3
        result = self.review(values)
        self.assertEqual(result["findings"], [])
        self.assertEqual(len(result["transitions"]), 4)
        self.assertTrue(all(
            item["assessment"] == "adjacent_endpoints"
            for item in result["transitions"]
        ))

    def test_direct_nonadjacent_upshift_is_reviewed_after_confirmation(self):
        result = self.review([1] * 11 + [4] * 11)
        self.assertEqual(len(result["findings"]), 1)
        finding = result["findings"][0]
        self.assertEqual((finding["from_gear"], finding["to_gear"]), (1, 4))
        self.assertEqual(finding["activation_sample"], 21)
        self.assertAlmostEqual(finding["activation_seconds"], 1.05)
        self.assertEqual(finding["severity"], "review")
        self.assertEqual(finding["rule_status"], "provisional")

    def test_direct_nonadjacent_downshift_is_reviewed(self):
        result = self.review([5] * 11 + [2] * 11)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["to_gear"], 2)

    def test_brief_wrong_value_does_not_become_a_shift(self):
        result = self.review([1] * 3 + [4] + [2] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["transitions"][0]["assessment"], "adjacent_endpoints")
        self.assertEqual(
            result["transitions"][0]["intermediate_observations"][0]["value"], 4,
        )

    def test_user_neutral_spike_example_has_no_finding(self):
        result = self.review([0] * 3 + [2] + [1] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["transitions"][0]["assessment"], "adjacent_endpoints")

    def test_brief_intermediate_upshift_is_preserved_without_manufacturing_skip(self):
        result = self.review([2] * 3 + [3] + [4] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["transitions"][0]["assessment"], "brief_intermediate_evidence",
        )

    def test_brief_intermediate_downshift_is_preserved(self):
        result = self.review([5] * 3 + [4] + [3] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["transitions"][0]["assessment"], "brief_intermediate_evidence",
        )

    def test_complete_ordered_path_can_include_other_unconfirmed_spikes(self):
        result = self.review([2] * 3 + [3, 1, 4] + [5] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(
            result["transitions"][0]["assessment"], "brief_intermediate_evidence",
        )

    def test_incomplete_intermediate_path_still_produces_review(self):
        result = self.review([2] * 11 + [3] + [5] * 11)
        self.assertEqual(len(result["findings"]), 1)

    def test_brief_destination_never_qualifies(self):
        result = self.review([2] * 3 + [4, 4])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["transitions"], [])

    def test_missing_and_invalid_values_prevent_bridging(self):
        for value in ("", "bad", "nan", "inf"):
            with self.subTest(value=value):
                result = self.review([2] * 3 + [value] + [4] * 3)
                self.assertEqual(result["findings"], [])
                self.assertEqual(len(result["unassessed"]), 1)

    def test_unresolved_nonadjacent_transition_is_not_diagnosed_as_skip(self):
        for value in (-2, 7):
            with self.subTest(value=value):
                result = self.review([2] * 3 + [value] + [4] * 3)
                self.assertEqual(result["findings"], [])
                self.assertEqual(len(result["unassessed"]), 1)

    def test_fractional_adjacent_endpoints_do_not_generate_warning(self):
        result = self.review([2] * 3 + [2.6] + [3] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["transitions"][0]["assessment"], "adjacent_endpoints")

    def test_timestamp_gap_at_boundary_prevents_finding(self):
        result = self.review(
            [2] * 3 + [4] * 3,
            times=[0, 0.05, 0.10, 1.0, 1.05, 1.10],
        )
        self.assertEqual(result["findings"], [])
        self.assertIn("timestamp gap", result["unassessed"][0]["reason"])

    def test_gap_in_either_confirmation_window_prevents_finding(self):
        for times in (
            [0, 0.05, 1.0, 1.05, 1.10, 1.15],
            [0, 0.05, 0.10, 0.15, 1.0, 1.05],
        ):
            with self.subTest(times=times):
                result = self.review([2] * 3 + [4] * 3, times=times)
                self.assertEqual(result["findings"], [])
                self.assertEqual(len(result["unassessed"]), 1)

    def test_old_gap_does_not_invalidate_later_contiguous_source_confirmation(self):
        values = [1] * 14 + [4] * 11
        result = self.review(values, times=[index / 20 + (.9 if index >= 2 else 0) for index in range(len(values))])
        self.assertEqual(len(result["findings"]), 1)

    def test_neutral_endpoints_are_separate_from_findings(self):
        for values in ([0] * 3 + [2] * 3, [2] * 3 + [0] * 3):
            with self.subTest(values=values):
                result = self.review(values)
                self.assertEqual(result["findings"], [])
                self.assertEqual(result["transitions"][0]["assessment"], "smaller_skip_note")
                self.assertEqual(len(result["notes"]), 1)

    def test_repeated_gear_with_brief_spike_does_not_count_as_shift(self):
        result = self.review([2] * 3 + [5] + [2] * 3)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["transitions"][0]["assessment"], "same_endpoints")

    def test_constant_run_does_not_manufacture_transition(self):
        result = self.review([0] * 20)
        self.assertTrue(result["available"])
        self.assertEqual(result["transitions"], [])
        self.assertEqual(result["findings"], [])

    def test_unavailable_timing_prevents_finding(self):
        result = evaluate_gear_transitions(
            make_states([2] * 3 + [4] * 3),
            {"available": False}, self.rules,
        )
        self.assertFalse(result["available"])
        self.assertEqual(result["findings"], [])

    def test_incomplete_or_unusable_timestamps_are_unavailable(self):
        for times in (
            [0, 0.05],
            [0, 0.05, 0.10, 0.10, 0.20, 0.25],
            [0, 0.05, 0.10, float("nan"), 0.20, 0.25],
        ):
            with self.subTest(times=times):
                result = self.review([2] * 3 + [4] * 3, times=times)
                self.assertFalse(result["available"])
                self.assertEqual(result["findings"], [])

    def test_estimated_timing_is_labelled_on_finding(self):
        result = self.review([1] * 11 + [4] * 11, basis="estimated")
        self.assertEqual(result["findings"][0]["time_basis"], "estimated")

    def test_source_state_evidence_is_not_modified(self):
        states = make_states([2] * 3 + [3] + [4] * 3)
        original = copy.deepcopy(states)
        timing = {
            "available": True, "basis": "recorded",
            "seconds": [index / 20 for index in range(7)],
        }
        evaluate_gear_transitions(states, timing, self.rules)
        self.assertEqual(states, original)


if __name__ == "__main__":
    unittest.main()
