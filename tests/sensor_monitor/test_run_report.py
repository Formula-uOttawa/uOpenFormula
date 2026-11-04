import copy
import json
import re
import tempfile
import unittest

from core.sensor_monitor.gear_report import analyze_gear
from core.sensor_monitor.run_report import build_run_report, save_run_report
from core.sensor_monitor.run_report_html import render_run_report
from core.sensor_monitor.sensor_catalog import SENSORS
from .test_gear_report import make_run, RULES
from core.sensor_monitor.timing import build_timing


def suite(run, allow_estimated=False):
    timing = build_timing(run, allow_estimated=allow_estimated)
    gear = analyze_gear(run, timing, RULES)
    return build_run_report(run, timing, gear)


class RunReportTests(unittest.TestCase):
    def test_nine_channels_and_separate_brake_circuits(self):
        run = make_run([1] * 10 + [2] * 10)
        for definition in SENSORS[1:]:
            run["channels"].append(definition["channel"])
            run["units"][definition["channel"]] = "bar"
            for row in run["data"]:
                row[definition["channel"]] = "1"
        report = suite(run)
        self.assertEqual(report["summary"]["counts"], {"review": 0, "no_findings": 1, "not_assessed": 8, "not_logged": 0})
        self.assertEqual([sensor["id"] for sensor in report["sensors"]][1:3], ["brake_front", "brake_rear"])

    def test_absent_channels_are_not_fabricated(self):
        report = suite(make_run([1] * 10 + [2] * 10))
        for sensor in report["sensors"][1:]:
            self.assertEqual(sensor["status"], "not_logged")
            self.assertEqual(sensor["values"], [])
            self.assertIsNone(sensor["data_summary"])

    def test_present_blank_and_nonfinite_data_are_not_healthy_or_zero(self):
        run = make_run([1] * 3 + [2] * 3)
        run["channels"].append("ECU FUEL P")
        for row, value in zip(run["data"], ("", "NaN", "inf", "bad", "0", "2")):
            row["ECU FUEL P"] = value
        fuel = suite(run)["sensors"][6]
        self.assertEqual(fuel["status"], "not_assessed")
        self.assertEqual(fuel["values"], [None, None, None, None, 0.0, 2.0])
        self.assertEqual(fuel["data_summary"]["missing_samples"], 1)
        self.assertEqual(fuel["data_summary"]["invalid_samples"], 3)
        self.assertEqual(fuel["data_summary"]["median"], 1)

    def test_findings_remain_review_even_with_insufficient_gear_coverage(self):
        report = suite(make_run([1] * 11 + [4] * 11 + [""] * 30))
        sensor = report["sensors"][0]
        self.assertEqual(sensor["analysis"]["overall"]["status"], "insufficient_evidence")
        self.assertEqual(sensor["status"], "review")
        self.assertEqual(report["summary"]["finding_count"], 2)

    def test_unusable_gear_data_are_not_assessed(self):
        gear = suite(make_run(["bad"] * 20))["sensors"][0]
        self.assertEqual(gear["status"], "not_assessed")

    def test_sample_axis_and_opt_in_estimate_remain_explicit(self):
        run = make_run([0] * 20, times=[""] * 20)
        index_report = suite(run)
        self.assertEqual(index_report["timing"]["basis"], "sample_index")
        self.assertEqual(index_report["timing"]["axis"], list(range(20)))
        estimated = suite(run, allow_estimated=True)
        self.assertEqual(estimated["timing"]["basis"], "estimated")
        self.assertAlmostEqual(estimated["timing"]["first_to_last_span"], .95)

    def test_recorded_gaps_are_available_to_break_the_graph(self):
        times = [0, .05, .1, 4, 4.05, 4.1]
        report = suite(make_run([1] * 3 + [2] * 3, times=times))
        self.assertEqual(report["timing"]["gap_after_sample"], [2])

    def test_report_is_independent_of_input_and_gear_result(self):
        run = make_run([2] * 10 + [4] * 10)
        original = copy.deepcopy(run)
        timing = build_timing(run)
        gear = analyze_gear(run, timing, RULES)
        report = build_run_report(run, timing, gear)
        report["sensors"][0]["analysis"]["analysis_settings"]["rules"]["confirmation_samples"] = 100
        self.assertEqual(gear["analysis_settings"]["rules"]["confirmation_samples"], 3)
        self.assertEqual(run, original)

    def test_html_and_json_round_trip_offline_without_overwriting(self):
        report = suite(make_run([2] * 10 + [4] * 10))
        with tempfile.TemporaryDirectory() as directory:
            first, second = save_run_report(report, directory), save_run_report(report, directory)
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads(first["json"].read_text()), report)
            html = first["html"].read_text()
            payload = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S).group(1)
            self.assertEqual(json.loads(payload), report)
            self.assertNotIn('<script src=', html)
            self.assertNotIn('https://', html)

    def test_csv_text_cannot_close_json_script_element(self):
        run = make_run([0] * 20)
        attack = '</script><script>alert("csv")</script>&\u2028'
        run["metadata"]["Session"] = attack
        run["source"] = attack
        html = render_run_report(suite(run))
        self.assertNotIn(attack, html)
        payload = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(payload)["source"]["session"], attack)


if __name__ == "__main__":
    unittest.main()
