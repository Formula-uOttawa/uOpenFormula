from types import SimpleNamespace
import unittest
from unittest.mock import patch
import matplotlib.pyplot as plt
from core.sensor_monitor.gear_plot import plot_gear
from .test_gear_report import make_report


class GearPlotReportTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def plot(self, values, **kwargs):
        run, report = make_report(values, **kwargs)
        with patch("core.sensor_monitor.gear_plot.plt.show"):
            figure = plot_gear(run, report)
        return figure, report

    def test_plot_uses_combined_assessment_and_finding_id(self):
        figure, report = self.plot([1] * 11 + [4] * 11)
        self.assertIn(report["overall"]["summary"], figure._suptitle.get_text())
        self.assertIn("GEAR-001", figure.axes[1].get_title())
        markers = [item for item in figure.axes[0].collections
                   if item.get_label() == "Review finding (click to inspect)"]
        self.assertEqual(markers[0].get_offsets().tolist(), [[21, 0.95]])

    def test_clicking_second_finding_updates_detail_panel(self):
        figure, report = self.plot([1] * 11 + [4] * 11 + [1] * 11)
        marker = next(item for item in figure.axes[0].collections
                      if item.get_label() == "Review finding (click to inspect)")
        event = SimpleNamespace(artist=marker, ind=[1], canvas=figure.canvas, name="pick_event")
        figure.canvas.callbacks.process("pick_event", event)
        self.assertIn("GEAR-002", figure.axes[1].get_title())

    def test_reverse_duration_is_shown_as_observation_without_warning(self):
        figure, report = self.plot([2] * 10 + [-1] * 25 + [2] * 10)
        self.assertIn("0 review finding(s)", figure._suptitle.get_text())
        labels = figure.axes[0].get_legend_handles_labels()[1]
        self.assertIn("Reverse gear (-1)", labels)
        self.assertNotIn("Review finding (click to inspect)", labels)

    def test_whole_run_result_shown_without_timing(self):
        figure, report = self.plot([0] * 20, times=[""] * 20)
        self.assertEqual(report["overall"]["status"], "review")
        self.assertIn("Timing: unavailable", figure._suptitle.get_text())


if __name__ == "__main__":
    unittest.main()
