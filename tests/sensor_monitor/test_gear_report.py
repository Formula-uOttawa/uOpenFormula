import copy
import json
import unittest

from core.sensor_monitor.gear_report import analyze_gear, format_gear_report, _evidence_sample_count
from core.sensor_monitor.timing import build_timing
from core.sensor_monitor.gear_rules import load_gear_rules

RULES = load_gear_rules()
RULES["version"] = "test"


def make_run(values, times=None):
    if times is None:
        times = [index / 20 for index in range(len(values))]
    return {
        "source": "synthetic.csv", "channels": ["Time", "Gear Position", "ECU RPM"],
        "units": {"Time": "s", "Gear Position": "gear", "ECU RPM": "rpm"},
        "metadata": {"Sample Rate": "20", "Duration": str(len(values) / 20), "Session": "Test"},
        "data": [{"Time": str(time), "Gear Position": str(value), "ECU RPM": "3000"}
                 for time, value in zip(times, values)],
    }


def make_report(values, shifts_expected=None, times=None):
    run = make_run(values, times=times)
    timing = build_timing(run) if values else {"available": False, "reason": "Empty recording."}
    return run, analyze_gear(run, timing, RULES, shifts_expected=shifts_expected)


class CombinedReportTests(unittest.TestCase):
    def test_reverse_is_a_normal_confirmable_state_without_duration_warning(self):
        run, report = make_report([2] * 10 + [-1] * 25 + [2] * 10)
        self.assertEqual(report["data_summary"]["confirmed_gears"], [-1, 2])
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["overall"]["status"], "no_issues_detected")
        self.assertEqual(report["observations"]["intervals"][0]["kind"], "Reverse gear (-1)")
        self.assertAlmostEqual(report["observations"]["intervals"][0]["elapsed_span_seconds"], 1.2)
        self.assertEqual(len(report["check_details"]["forward_sequence"]["reverse_not_checked"]), 2)

    def test_reverse_only_stationary_test_has_no_warning(self):
        run, report = make_report([-1] * 30, shifts_expected=False)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["data_summary"]["confirmed_gears"], [-1])
        self.assertIn("Reverse", format_gear_report(report))

    def test_reverse_only_run_can_still_trigger_expected_shifting_check(self):
        run, report = make_report([-1] * 30, shifts_expected=True)
        self.assertEqual(len(report["findings"]), 1)
        self.assertEqual(report["findings"][0]["check_id"], "whole_run_no_shift")
        self.assertIn("reverse", report["findings"][0]["message"].lower())

    def test_forward_skip_contains_evidence_locations_and_settings(self):
        run, report = make_report([1] * 11 + [4] * 11)
        finding = report["findings"][0]
        self.assertEqual(finding["id"], "GEAR-001")
        self.assertEqual(finding["scope"], "local_event")
        self.assertEqual(finding["location"]["start_sample"], 10)
        self.assertEqual(finding["location"]["end_sample"], 21)
        self.assertEqual(finding["location"]["activation_sample"], 21)
        self.assertEqual(finding["evidence"]["rule_result"]["to_gear"], 4)
        self.assertTrue(finding["evidence"]["sample_window"])
        self.assertEqual(report["analysis_settings"]["rules"], RULES)
        self.assertEqual(report["overall"]["summary"], "Localized findings to review")

    def test_normal_recording_is_not_claimed_fully_assessed(self):
        run, report = make_report([1] * 10 + [2] * 10)
        self.assertEqual(report["overall"]["finding_count"], 0)
        self.assertEqual(report["overall"]["assessment_scope"], "limited")
        self.assertEqual(report["checks"][-1]["outcome"], "not_triggered")
        self.assertEqual(report["gear_mapping"]["maximum_forward_gear"], 6)
        self.assertEqual(report["gear_mapping"]["maximum_forward_gear_status"], "assumed")

    def test_unavailable_timing_keeps_global_observation_and_marks_sequence_unassessed(self):
        run = make_run([0] * 20, times=[""] * 20)
        report = analyze_gear(run, build_timing(run), RULES)
        self.assertEqual(report["checks"][0]["outcome"], "unassessed")
        self.assertEqual(len(report["findings"]), 1)
        self.assertIsNone(report["findings"][0]["location"]["start_seconds"])

    def test_estimated_timing_is_explicit(self):
        run = make_run([1] * 11 + [4] * 11, times=[""] * 22)
        report = analyze_gear(run, build_timing(run, allow_estimated=True), RULES)
        self.assertEqual(report["findings"][0]["location"]["time_basis"], "estimated")
        self.assertTrue(any("uniform sampling" in text for text in report["limitations"]))

    def test_sparse_or_invalid_data_does_not_produce_healthy_summary(self):
        for values in ([0] * 10 + [""] * 10, ["bad", "nan", "inf"]):
            with self.subTest(values=values):
                run, report = make_report(values)
                self.assertEqual(report["overall"]["status"], "insufficient_evidence")
                json.dumps(report, allow_nan=False)

    def test_missing_channel_has_report_without_crash(self):
        run = make_run([0] * 20)
        run["channels"].remove("Gear Position")
        for row in run["data"]:
            del row["Gear Position"]
        report = analyze_gear(run, build_timing(run), RULES)
        self.assertFalse(report["data_summary"]["channel_available"])
        self.assertEqual(report["overall"]["status"], "insufficient_evidence")
        self.assertEqual(report["findings"], [])

    def test_brief_wrong_gear_stays_in_evidence_without_skip(self):
        run, report = make_report([1] * 10 + [4] + [2] * 10)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["observations"]["brief_state_blocks"][0]["value"], 4)

    def test_report_does_not_mutate_run_or_rule_settings(self):
        run = make_run([2] * 10 + [4] * 10)
        original = copy.deepcopy(run)
        rules = copy.deepcopy(RULES)
        report = analyze_gear(run, build_timing(run), rules)
        report["analysis_settings"]["rules"]["confirmation_samples"] = 99
        self.assertEqual(run, original)
        self.assertEqual(rules, RULES)

    def test_findings_survive_when_overall_data_coverage_is_insufficient(self):
        run, report = make_report([1] * 11 + [4] * 11 + [""] * 30)
        self.assertEqual(report["overall"]["status"], "insufficient_evidence")
        self.assertEqual(len(report["findings"]), 2)

    def test_evidence_coverage_does_not_double_count_overlap(self):
        findings = [{"location": {"start_sample": start, "end_sample": end}}
                    for start, end in ((2, 5), (4, 8), (10, 10))]
        self.assertEqual(_evidence_sample_count(findings), 8)

    def test_formatter_has_consistent_ids_counts_and_optional_details(self):
        run, report = make_report([1] * 11 + [4] * 11)
        text = format_gear_report(report)
        self.assertIn("Review findings: 1", text)
        self.assertIn("GEAR-001", text)
        self.assertIn("ASSESSMENT LIMITATIONS", text)
        self.assertNotIn("RECORDED VALUE DISTRIBUTION", text)
        self.assertIn("RECORDED VALUE DISTRIBUTION", format_gear_report(report, detailed=True))


if __name__ == "__main__":
    unittest.main()
