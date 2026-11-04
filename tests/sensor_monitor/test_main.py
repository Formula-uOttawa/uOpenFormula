import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from core.sensor_monitor import __main__ as main
from .test_gear_report import make_run


class MainReportTests(unittest.TestCase):
    def execute(self, values, answer="y", times=None, **options):
        run = make_run(values, times=[""] * len(values) if times is None else times)
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with (patch("core.sensor_monitor.__main__.load_csv", return_value=run),
                  patch("builtins.input", side_effect=["synthetic.csv", answer]),
                  patch("core.sensor_monitor.__main__.webbrowser.open", return_value=True) as browser,
                  redirect_stdout(output)):
                report = main.main(report_dir=directory, **options)
            files = list(Path(directory).glob("*.json"))
            self.assertEqual(len(files), 1)
            self.assertEqual(json.loads(files[0].read_text()), report)
            html = next(Path(directory).glob("*.html"))
            self.assertIn("Sensor run review", html.read_text())
            if options.get("open_report", True):
                browser.assert_called_once_with(html.resolve().as_uri())
            else:
                browser.assert_not_called()
        return output.getvalue(), report

    @staticmethod
    def gear(report):
        return next(sensor for sensor in report["sensors"] if sensor["id"] == "gear")

    def test_normal_run_prints_saves_and_opens_the_suite_report(self):
        output, report = self.execute([1] * 10 + [2] * 10)
        self.assertIn("SENSOR RUN REPORT", output)
        self.assertIn("Saved HTML report:", output)
        self.assertEqual(len(report["sensors"]), 9)
        self.assertEqual(self.gear(report)["status"], "no_findings")

    def test_reverse_is_normal(self):
        output, report = self.execute([2] * 10 + [-1] * 25 + [2] * 10)
        self.assertEqual(self.gear(report)["findings"], [])
        self.assertEqual(self.gear(report)["status"], "no_findings")

    def test_constant_neutral_respects_recording_purpose(self):
        output, report = self.execute([0] * 20)
        self.assertEqual(self.gear(report)["status"], "review")
        output, report = self.execute([0] * 20, shifts_expected=False)
        self.assertEqual(self.gear(report)["findings"], [])

    def test_declined_time_uses_sample_index_and_keeps_finding(self):
        output, report = self.execute([0] * 20, answer="n")
        self.assertEqual(report["timing"]["basis"], "sample_index")
        finding = self.gear(report)["findings"][0]
        self.assertIsNone(finding["location"]["start_seconds"])

    def test_bad_timestamps_do_not_get_replaced_with_estimates(self):
        output, report = self.execute([0] * 20, times=["0"] + [""] * 19)
        self.assertEqual(report["timing"]["basis"], "sample_index")
        self.assertIn("Timestamps are partially missing", output)

    def test_forward_skip_is_in_suite(self):
        output, report = self.execute([1] * 11 + [4] * 11)
        self.assertIn("GEAR-001", output)
        self.assertEqual(self.gear(report)["findings"][0]["check_id"], "forward_sequence")

    def test_no_open_preserves_export(self):
        output, report = self.execute([1] * 10 + [2] * 10, open_report=False)
        self.assertEqual(report["summary"]["finding_count"], 0)

    def test_save_failure_does_not_try_to_open_a_missing_report(self):
        output = io.StringIO()
        with (patch("core.sensor_monitor.__main__.load_csv", return_value=make_run([1] * 10 + [2] * 10)),
              patch("core.sensor_monitor.__main__.save_run_report", side_effect=OSError("not writable")),
              patch("core.sensor_monitor.__main__.webbrowser.open") as browser, redirect_stdout(output)):
            report = main.main("synthetic.csv")
        self.assertIn("Could not save the report", output.getvalue())
        self.assertIsNotNone(report)
        browser.assert_not_called()

    def test_browser_failure_keeps_saved_files_and_prints_fallback(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with (patch("core.sensor_monitor.__main__.load_csv", return_value=make_run([0] * 20)),
                  patch("core.sensor_monitor.__main__.webbrowser.open", side_effect=OSError("no browser")), redirect_stdout(output)):
                main.main("synthetic.csv", report_dir=directory)
            self.assertEqual(len(list(Path(directory).glob("*.html"))), 1)
        self.assertIn("Open the saved HTML file", output.getvalue())

    def test_estimate_option_does_not_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            with (patch("core.sensor_monitor.__main__.load_csv", return_value=make_run([0] * 20, times=[""] * 20)),
                  patch("builtins.input") as prompt, redirect_stdout(io.StringIO())):
                report = main.main("synthetic.csv", estimate_time=True, open_report=False, report_dir=directory)
        prompt.assert_not_called()
        self.assertEqual(report["timing"]["basis"], "estimated")

    def test_load_failure_is_clear(self):
        output = io.StringIO()
        with patch("core.sensor_monitor.__main__.load_csv", side_effect=OSError("missing file")), redirect_stdout(output):
            self.assertIsNone(main.main("missing.csv"))
        self.assertIn("Could not load the recording", output.getvalue())


if __name__ == "__main__":
    unittest.main()
