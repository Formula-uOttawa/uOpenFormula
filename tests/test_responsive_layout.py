import io
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

import dearpygui.dearpygui as dpg

from core.data_manager import DataManager
from ui.home_page import HomePage


class ResponsiveLayoutTests(unittest.TestCase):
    def setUp(self):
        dpg.create_context()
        dpg.create_viewport(width=1280, height=800)
        self.page = HomePage.__new__(HomePage)
        self.page.importer = DataManager()
        self.page.df = None
        self.page.file_path = ''
        self.page.init_menu_bar()
        sample = Path(__file__).resolve().parents[1] / '_debugging_files/USE_THESE/faran_a_3731.csv'
        with redirect_stdout(io.StringIO()):
            self.assertTrue(self.page._load_project_file(sample))
        self.monitor = self.page.views['elec_monitor']

    def tearDown(self):
        dpg.destroy_context()

    def resize(self, width, height, menu=20):
        with patch.object(self.page, '_viewport_geometry', return_value=(width, height, menu)):
            self.page._resize_layout()

    def test_navigation_and_all_analysis_panes_follow_client_area_below_menu(self):
        with patch('ui.home_page.dpg.configure_item', wraps=dpg.configure_item) as configure:
            self.resize(1600, 1000, 24)
        configure.assert_any_call('navbar', pos=(0, 24), width=200, height=976)
        nav = dpg.get_item_configuration('navbar')
        self.assertEqual((nav['width'], nav['height']), (200, 976))
        for tag in self.page.SWAPPABLE_WINDOWS:
            pane = dpg.get_item_configuration(tag)
            self.assertEqual((pane['width'], pane['height']), (1400, 976), tag)
            configure.assert_any_call(tag, pos=(200, 24), width=1400, height=976)

    def test_resize_adjusts_text_and_plot_without_reanalysis_or_replacing_axes(self):
        report = self.monitor.report
        self.monitor._select_sensor(None, None, 'brake_front')
        children = dpg.get_item_children('sensor_monitor_selected_plot')
        with patch('ui.views.elec_monitor.analyze_loaded_recording', side_effect=AssertionError('Resize must not reanalyze')):
            self.resize(1600, 1000)
        self.assertIs(self.monitor.report, report)
        self.assertEqual(self.monitor.selected_id, 'brake_front')
        self.assertEqual(dpg.get_item_children('sensor_monitor_selected_plot'), children)
        plot = dpg.get_item_configuration('sensor_monitor_selected_plot')
        self.assertEqual(plot['height'], self.monitor._plot_height())
        self.assertEqual(plot['width'], -1)
        for item, column in self.monitor._wrapped_text.items():
            expected = self.monitor._wrap_width() if column is None else self.monitor._column_width(column)
            self.assertEqual(dpg.get_item_configuration(item)['wrap'], expected)

    def test_compact_window_shrinks_content_and_preserves_sensor_results(self):
        report = self.monitor.report
        self.resize(1600, 1000)
        large_height = dpg.get_item_configuration('sensor_monitor_selected_plot')['height']
        self.resize(960, 640)
        self.assertEqual(self.monitor._content_size, (760, 620))
        self.assertLess(dpg.get_item_configuration('sensor_monitor_selected_plot')['height'], large_height)
        self.assertEqual(dpg.get_item_configuration('sensor_monitor_mini_gear')['width'], -1)
        self.assertIs(self.monitor.report, report)
        self.resize(0, 0)
        self.assertEqual(self.monitor._content_size, (760, 620))

    def test_existing_raw_table_and_oil_plots_fill_their_parent_panels(self):
        raw = dpg.get_item_configuration('show_data')
        self.assertEqual((raw['width'], raw['height']), (-1, -1))
        table = dpg.get_item_children('show_data', 1)[0]
        table_config = dpg.get_item_configuration(table)
        self.assertEqual((table_config['width'], table_config['height']), (-1, -1))
        for tag in ('Rpm & Oil Pressure graph', 'G-forces & Oil Pressure graph',
                    'G-forces & Low Oil Pressure plot', 'Rpm vs Oil Pressure plot',
                    'Oil Starvation distrobution Graph'):
            plot = dpg.get_item_children(tag, 1)[0]
            config = dpg.get_item_configuration(plot)
            self.assertEqual((config['width'], config['height']), (-1, -1), tag)


if __name__ == '__main__':
    unittest.main()
