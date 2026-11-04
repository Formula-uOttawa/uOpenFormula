import copy
import json
import unittest

from core.sensor_monitor.gear_quality import evaluate_gear_quality
from core.sensor_monitor.gear_report import analyze_gear
from core.sensor_monitor.gear_states import build_gear_states
from core.sensor_monitor.gear_transitions import evaluate_gear_transitions
from core.sensor_monitor.run_report import build_run_report
from .test_gear_report import make_run, RULES
from core.sensor_monitor.timing import build_timing


class PersistentDataTests(unittest.TestCase):
    def review(self, values, times=None, timing=None, **changes):
        rules = {**RULES, **changes}
        run = make_run(values, times=times)
        clock = build_timing(run) if timing is None else timing
        return evaluate_gear_quality(run, clock, rules)

    def test_twenty_rows_do_not_span_one_second_but_twenty_one_do(self):
        self.assertEqual(self.review([1.94] * 20)["findings"], [])
        event = self.review([1.94] * 21)["findings"][0]
        self.assertEqual(event["activation_sample"], 20)
        self.assertAlmostEqual(event["elapsed_span_seconds"], 1)
        self.assertTrue(event["continues_at_file_end"])

    def test_changing_fractions_are_one_continuous_episode(self):
        result = self.review([1.1, 1.2, 1.3] * 7)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["category_counts"], {"fractional": 21})

    def test_allowed_reverse_neutral_and_six_do_not_trigger_bad_data(self):
        result = self.review([-1] * 25 + [0] * 25 + [6] * 25)
        self.assertEqual(result["findings"], [])

    def test_outside_numbers_are_unusable_and_never_confirmed(self):
        for value in (-2, 7, 100, 6.1):
            with self.subTest(value=value):
                event = self.review([value] * 21)["findings"][0]
                self.assertEqual(event["category_counts"], {"outside_range": 21})
                self.assertTrue(all(item["status"] == "unresolved"
                                    for item in build_gear_states(make_run([value] * 21))["intervals"]))

    def test_maximum_gear_is_configurable(self):
        self.assertEqual(self.review([7] * 21, maximum_forward_gear=7)["findings"], [])
        self.assertEqual(len(self.review([6] * 21, maximum_forward_gear=5)["findings"]), 1)

    def test_missing_invalid_and_nonfinite_data_are_not_zero_or_healthy(self):
        for value, kind in (("", "missing"), ("bad", "invalid"), ("nan", "invalid"), ("inf", "invalid")):
            with self.subTest(value=value):
                result = self.review([value] * 21)
                self.assertEqual(result["findings"][0]["category_counts"], {kind: 21})
                json.dumps(result, allow_nan=False)

    def test_mixed_unusable_categories_make_one_finding(self):
        result = self.review([1.5, 7, "", "nan"] * 6)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["sample_count"], 24)
        self.assertEqual(set(result["findings"][0]["category_counts"]), {"fractional", "outside_range", "missing", "invalid"})

    def test_valid_sample_and_timestamp_gap_break_episodes(self):
        self.assertEqual(self.review([1.5] * 11 + [2] + [1.5] * 11)["findings"], [])
        times = [index / 20 + (1 if index >= 11 else 0) for index in range(21)]
        result = self.review([1.5] * 21, times=times)
        self.assertEqual(result["findings"], [])
        self.assertEqual(len(result["intervals"]), 2)
        self.assertEqual(result["timestamp_gap_count"], 1)

    def test_missing_clock_retains_observations_without_inventing_duration(self):
        result = self.review([1.94] * 100, timing={"available": False, "reason": "No timestamps."})
        self.assertFalse(result["available"])
        self.assertEqual(result["findings"], [])
        self.assertIsNone(result["intervals"][0]["elapsed_span_seconds"])

    def test_duration_works_at_another_sampling_rate(self):
        self.assertEqual(len(self.review([1.5] * 11, times=[index / 10 for index in range(11)])["findings"]), 1)
        self.assertEqual(self.review([1.5] * 21, times=[index / 100 for index in range(21)])["findings"], [])

    def test_near_integer_is_preserved_and_assessed_without_rounding(self):
        self.assertEqual(self.review([1.9999] * 21)["findings"][0]["example_values"], ["1.9999"])

    def test_persistent_bad_data_remains_visible_with_no_confirmed_gears(self):
        run = make_run(["bad"] * 21)
        clock = build_timing(run)
        gear = analyze_gear(run, clock, RULES)
        suite = build_run_report(run, clock, gear)
        self.assertEqual(suite["sensors"][0]["status"], "review")
        self.assertEqual(gear["findings"][0]["check_id"], "gear_signal_quality")
        json.dumps(suite, allow_nan=False)


class LargeChangeTests(unittest.TestCase):
    def review(self, values, times=None, **changes):
        rules = {**RULES, **changes}
        run = make_run(values, times=times)
        return evaluate_gear_transitions(build_gear_states(run, rules["confirmation_samples"], rules["maximum_forward_gear"]),
                                         build_timing(run), rules)

    def test_neutral_and_forward_large_changes_are_reviewed_both_directions(self):
        for start, end in ((0, 3), (5, 2), (0, 5), (5, 0)):
            with self.subTest(start=start, end=end):
                result = self.review([start] * 11 + [end] * 11)
                self.assertEqual(len(result["findings"]), 1)
                self.assertEqual(result["findings"][0]["activation_sample"], 21)

    def test_small_skips_are_notes_and_do_not_make_the_suite_review(self):
        run = make_run([0] * 21 + [2] * 21)
        report = analyze_gear(run, build_timing(run), RULES)
        self.assertEqual(report["findings"], [])
        self.assertEqual(len(report["notes"]), 1)
        self.assertEqual(report["notes"][0]["severity"], "info")
        self.assertEqual(report["overall"]["note_count"], 1)

    def test_three_row_spike_does_not_become_a_large_change_review(self):
        result = self.review([0] * 21 + [5] * 3 + [0] * 21)
        self.assertEqual(result["findings"], [])

    def test_larger_window_never_erases_a_confirmed_intermediate_gear(self):
        values = [5] * 21 + [3] * 9 + [2] * 21
        result = self.review(values)
        self.assertEqual(result["findings"], [])
        self.assertEqual([(item["from_gear"], item["to_gear"]) for item in result["transitions"]], [(5, 3), (3, 2)])

    def test_stricter_windows_cannot_manufacture_new_jump_pairs(self):
        values = [0] * 21 + [3] * 5 + [5] * 41 + [0] * 41
        previous = None
        for threshold in (.1, .2, .5, 1):
            result = self.review(values, large_jump_endpoint_seconds=threshold)
            pairs = {(item["start_sample"], item["end_sample"], item["from_gear"], item["to_gear"]) for item in result["findings"]}
            if previous is not None:
                self.assertLessEqual(pairs, previous)
            previous = pairs

    def test_brief_fraction_does_not_hide_a_sustained_large_change(self):
        result = self.review([0] * 21 + [2.4] + [5] * 21)
        self.assertEqual(len(result["findings"]), 1)

    def test_missing_outside_or_persistent_bad_patch_is_not_bridged(self):
        for middle in ([""], [7], [2.4] * 21):
            with self.subTest(middle=middle):
                result = self.review([0] * 21 + middle + [5] * 21)
                self.assertEqual(result["findings"], [])
                self.assertEqual(len(result["unassessed"]), 1)

    def test_reverse_is_not_an_arithmetic_gear_distance(self):
        result = self.review([-1] * 21 + [5] * 21)
        self.assertEqual(result["findings"], [])
        self.assertEqual(len(result["reverse_not_checked"]), 1)

    def test_gap_during_the_extended_endpoint_window_prevents_review(self):
        values = [0] * 21 + [5] * 21
        times = [index / 20 + (1 if index >= 27 else 0) for index in range(len(values))]
        result = self.review(values, times=times)
        self.assertEqual(result["findings"], [])
        self.assertEqual(len(result["unassessed"]), 1)

    def test_complete_one_sample_intermediate_path_is_preserved(self):
        result = self.review([0] * 21 + [1, 2] + [3] * 21)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["transitions"][0]["assessment"], "brief_intermediate_evidence")


class ReportContextTests(unittest.TestCase):
    def test_no_shift_records_gps_context_without_assuming_shifts_were_required(self):
        run = make_run([0] * 41)
        run["channels"].append("GPS Speed")
        run["units"]["GPS Speed"] = "km/h"
        for index, row in enumerate(run["data"]):
            row["GPS Speed"] = str(index * 2.5)
        report = analyze_gear(run, build_timing(run), RULES)
        event = report["findings"][0]
        self.assertEqual(event["category"], "run_observation")
        self.assertEqual(event["evidence"]["rule_result"]["gps_context"]["maximum"], 100)
        self.assertIn("expected is unknown", event["message"])
        self.assertIn("does not establish", event["message"])

    def test_short_legitimate_change_still_prevents_whole_run_no_shift(self):
        run = make_run([2] * 200 + [3] * 4 + [2] * 200)
        report = analyze_gear(run, build_timing(run), RULES)
        self.assertEqual(report["check_details"]["whole_run_no_shift"]["assessment"], "multiple_gears_observed")
        self.assertFalse(any(item["check_id"] == "whole_run_no_shift" for item in report["findings"]))

    def test_new_brake_aliases_show_real_values_and_source_names(self):
        run = make_run([1] * 11 + [2] * 11)
        for channel, value in (("BRK PRESS F", "12"), ("BRK PRESS R", "7")):
            run["channels"].append(channel)
            run["units"][channel] = "bar"
            for row in run["data"]:
                row[channel] = value
        gear = analyze_gear(run, build_timing(run), RULES)
        report = build_run_report(run, build_timing(run), gear)
        self.assertEqual([item["channel"] for item in report["sensors"][1:3]], ["BRK PRESS F", "BRK PRESS R"])
        self.assertEqual([item["data_summary"]["median"] for item in report["sensors"][1:3]], [12, 7])

    def test_ambiguous_brake_aliases_are_not_silently_selected(self):
        run = make_run([1] * 11 + [2] * 11)
        run["channels"] += ["Front Brake Pres", "BRK PRESS F"]
        gear = analyze_gear(run, build_timing(run), RULES)
        with self.assertRaisesRegex(ValueError, "Ambiguous channels"):
            build_run_report(run, build_timing(run), gear)

    def test_source_rows_and_rules_are_not_modified_by_analysis(self):
        run = make_run([1.94] * 21)
        original, rules = copy.deepcopy(run), copy.deepcopy(RULES)
        analyze_gear(run, build_timing(run), rules)
        self.assertEqual(run, original)
        self.assertEqual(rules, RULES)


if __name__ == "__main__":
    unittest.main()
