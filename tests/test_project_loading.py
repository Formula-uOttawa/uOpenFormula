import csv
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dearpygui.dearpygui as dpg

from core.data_manager import DataManager
from tests.sensor_monitor.test_gear_report import make_run
from ui.home_page import HomePage


class ProjectLoadingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = self.recording('first.csv', [1] * 11 + [4] * 11)
        dpg.create_context()
        dpg.create_viewport(width=1440, height=1000)
        with dpg.window(tag='Landing Page'):
            dpg.add_text('landing content')
        self.page = HomePage.__new__(HomePage)
        self.page.importer = DataManager()
        self.page.df = None
        self.page.file_path = ''
        self.output = io.StringIO()

    def tearDown(self):
        dpg.destroy_context()
        self.directory.cleanup()

    def recording(self, name, values):
        run = make_run(values)
        path = Path(self.directory.name) / name
        with path.open('w', newline='') as stream:
            writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
            writer.writerows(run['metadata'].items())
            writer.writerow(['Time', '12:00 PM'])
            writer.writerow(run['channels'])
            writer.writerow([run['units'][channel] for channel in run['channels']])
            writer.writerows([row[channel] for channel in run['channels']] for row in run['data'])
        return path

    def load(self, path):
        with redirect_stdout(self.output):
            return self.page._load_project_file(path)

    def test_mac_landing_and_menu_loaders_never_create_tk(self):
        with patch('ui.home_page.sys.platform', 'darwin'), patch('ui.home_page.tk.Tk', side_effect=AssertionError('Tk causes a native Mac crash')):
            self.page.first_file_selection()
            self.assertFalse(hasattr(self.page, 'views'), 'Wait for asynchronous selection')
            callback = dpg.get_item_callback('csv_import_dialog')
            with redirect_stdout(self.output):
                callback('csv_import_dialog', {'file_path_name': str(self.path)})
            self.assertFalse(dpg.get_item_configuration('csv_import_dialog')['show'])
            self.assertEqual(self.page.file_path, str(self.path))
            self.page.select_file_tk()  # Same entry point used by File / Load Project.
            self.assertTrue(dpg.get_item_configuration('csv_import_dialog')['show'])

    def test_cancel_keeps_the_landing_page_and_does_not_import(self):
        with patch('ui.home_page.sys.platform', 'darwin'), patch('ui.home_page.dpg.file_dialog', wraps=dpg.file_dialog) as dialog:
            self.page.first_file_selection()
        dialog.call_args.kwargs['cancel_callback']('csv_import_dialog', {})
        self.assertIsNone(self.page.df)
        self.assertFalse(hasattr(self.page, 'views'))
        self.assertFalse(dpg.get_item_configuration('csv_import_dialog')['show'])
        self.assertTrue(dpg.get_item_children('Landing Page', 1))

    def test_native_cancel_destroys_tk_and_keeps_the_recording(self):
        self.assertTrue(self.load(self.path))
        manager = self.page.importer
        with patch('ui.home_page.sys.platform', 'win32'), patch('ui.home_page.tk.Tk') as root, patch('ui.home_page.filedialog.askopenfilename', return_value=''):
            self.assertFalse(self.page.select_file_tk())
        root.return_value.destroy.assert_called_once()
        self.assertIs(self.page.importer, manager)

    def test_shared_load_automatically_populates_monitor_without_a_second_picker(self):
        self.assertTrue(self.load(self.path))
        monitor = self.page.views['elec_monitor']
        self.assertIs(monitor.manager, self.page.importer)
        self.assertIsNone(monitor.source_path)
        self.assertEqual(monitor.report['source']['path'], str(self.path.resolve()))
        labels = [dpg.get_item_configuration(item).get('label') for item in dpg.get_all_items()]
        self.assertNotIn('Open CSV', labels)
        self.assertNotIn('Use project recording', labels)

    def test_missing_oil_channels_do_not_prevent_raw_data_or_monitor_from_opening(self):
        self.assertTrue(self.load(self.path))
        self.assertIn('raw_data', self.page.views)
        self.assertIn('elec_monitor', self.page.views)
        self.assertIn('ECU OIL P', self.page.view_errors['power_oilstarv'])
        self.assertTrue(dpg.does_item_exist('power_oilstarv'))
        self.page._switch_main_view('elec_monitor')

    def test_second_load_replaces_views_and_shared_manager_without_duplicate_tags(self):
        self.assertTrue(self.load(self.path))
        first_manager = self.page.importer
        first_monitor = self.page.views['elec_monitor']
        second = self.recording('second.csv', [2] * 15 + [3] * 15)
        self.assertTrue(self.load(second))
        monitor = self.page.views['elec_monitor']
        self.assertIsNot(self.page.importer, first_manager)
        self.assertIsNot(monitor, first_monitor)
        self.assertIs(monitor.manager, self.page.importer)
        self.assertEqual(monitor.report['source']['measurement_rows'], 30)
        self.assertEqual(monitor.report['source']['path'], str(second.resolve()))

    def test_failed_load_preserves_previous_data_and_views_and_displays_error(self):
        self.assertTrue(self.load(self.path))
        manager, frame, views = self.page.importer, self.page.df, self.page.views
        self.assertFalse(self.load(Path(self.directory.name) / 'missing.csv'))
        self.assertIs(self.page.importer, manager)
        self.assertIs(self.page.df, frame)
        self.assertIs(self.page.views, views)
        self.assertEqual(self.page.file_path, str(self.path))
        self.assertTrue(dpg.does_item_exist('project_load_error'))

    def test_failed_first_import_keeps_landing_page(self):
        invalid = Path(self.directory.name) / 'invalid.csv'
        invalid.write_text('not,a,recording\n')
        self.assertFalse(self.load(invalid))
        self.assertIsNone(self.page.df)
        self.assertTrue(dpg.get_item_children('Landing Page', 1))
        self.assertTrue(dpg.does_item_exist('project_load_error'))


if __name__ == '__main__':
    unittest.main()
