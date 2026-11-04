"""Navigation and display checks for the monitor inside the original app size."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import dearpygui.dearpygui as dpg

from core.sensor_monitor.service import analyze_run
from tests.sensor_monitor.test_gear_report import make_run
from ui.views.elec_monitor import MonitorView


class SensorMonitorLayoutTests(unittest.TestCase):
    def setUp(self):
        dpg.create_context()
        dpg.create_viewport(width=800, height=600)
        with dpg.window(tag='monitor_parent', pos=(200, 0), width=600, height=600):
            self.view = MonitorView(SimpleNamespace(path='', df=None))
            self.view.build('monitor_parent')
        self.view.report = analyze_run(make_run([1] * 11 + [4] * 11))
        self.view._render()

    def tearDown(self):
        dpg.destroy_context()

    def test_overview_and_details_use_separate_tabs_without_changing_viewport(self):
        self.assertEqual((dpg.get_viewport_width(), dpg.get_viewport_height()), (800, 600))
        self.assertEqual(len(dpg.get_item_children(self.view.TABLE, 0)), 2)
        self.assertEqual(len(dpg.get_item_children(self.view.TABLE, 1)), 9)
        self.assertEqual(dpg.get_item_configuration(self.view.TABLE)['height'], -1)
        self.assertEqual(dpg.get_item_parent(self.view.DETAIL), self.view.DETAIL_TAB)
        self.assertEqual(dpg.get_value(self.view.TABS), self.view.OVERVIEW_TAB)

    def test_sensor_selection_opens_detail_and_dropdown_switches_missing_channels(self):
        report = self.view.report
        with patch('ui.views.elec_monitor.analyze_loaded_recording', side_effect=AssertionError('Navigation must not analyze')):
            self.view._select_sensor(None, None, 'gear')
            self.assertEqual(dpg.get_value(self.view.TABS), self.view.DETAIL_TAB)
            self.assertEqual(dpg.get_value('sensor_monitor_sensor_selector'), 'Gear position')
            self.view._sensor_changed(None, 'Front brake pressure')
            self.assertEqual(self.view.selected_id, 'brake_front')
            self.assertFalse(dpg.does_item_exist('sensor_monitor_selected_plot'))
            self.view._sensor_changed(None, 'Gear position')
        self.assertTrue(dpg.does_item_exist('sensor_monitor_selected_plot'))
        self.assertIs(self.view.report, report)

    def test_options_keep_selected_tab_and_sensor_when_reanalyzing(self):
        self.view._select_sensor(None, None, 'brake_front')
        self.view._tab_changed(None, dpg.get_alias_id(self.view.OPTIONS_TAB))
        with patch('ui.views.elec_monitor.analyze_recording', return_value=self.view.report):
            self.view.source_path = 'recording.csv'
            self.view._reanalyze()
        self.assertEqual(dpg.get_value(self.view.TABS), self.view.OPTIONS_TAB)
        self.assertEqual(self.view.selected_id, 'brake_front')
        self.assertFalse(self.view.allow_estimated)
        self.assertIsNone(self.view.shifts_expected)

    def test_panel_resize_preserves_plot_objects_and_only_changes_monitor_widgets(self):
        self.view._select_sensor(None, None, 'gear')
        report = self.view.report
        axes = dpg.get_item_children('sensor_monitor_selected_plot')
        parent = dpg.get_item_configuration('monitor_parent')
        with patch('ui.views.elec_monitor.dpg.get_item_rect_size', return_value=(580, 550)):
            self.view._resize_content()
        self.assertEqual(dpg.get_item_configuration('monitor_parent'), parent)
        self.assertEqual((dpg.get_viewport_width(), dpg.get_viewport_height()), (800, 600))
        self.assertEqual(dpg.get_item_children('sensor_monitor_selected_plot'), axes)
        self.assertIs(self.view.report, report)
        self.assertEqual(self.view.selected_id, 'gear')
        for item, column in self.view._wrapped_text.items():
            expected = self.view._wrap_width() if column is None else self.view._column_width(column)
            self.assertEqual(dpg.get_item_configuration(item)['wrap'], expected)


if __name__ == '__main__':
    unittest.main()
