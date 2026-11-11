import csv
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from subprocess import CompletedProcess
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

    def test_mac_landing_and_menu_use_the_same_tk_process_and_importer(self):
        self.page.init_menu_bar()
        menu_callback = next(
            dpg.get_item_callback(item) for item in dpg.get_all_items()
            if dpg.get_item_label(item) == 'Load Project'
        )
        second = self.recording('second.csv', [2] * 12 + [3] * 12)

        for callback, path in ((self.page.first_file_selection, self.path), (menu_callback, second)):
            with self.subTest(path=path.name):
                with (
                    patch('ui.project_file_picker.sys.platform', 'darwin'),
                    patch('ui.project_file_picker.tk.Tk',
                          side_effect=AssertionError('Tk must open in its own process')),
                    patch('ui.project_file_picker.subprocess.run',
                          return_value=CompletedProcess([], 0, json.dumps(str(path)))) as picker,
                    redirect_stdout(self.output),
                ):
                    callback()
                picker.assert_called_once()
                self.assertEqual(picker.call_args.args[0][-1], '--choose-project-file')
                self.assertEqual(self.page.file_path, str(path))
                self.assertEqual(self.page.views['elec_monitor'].report['source']['path'], str(path.resolve()))

    def test_cancel_keeps_the_landing_page_and_does_not_import(self):
        with (
            patch('ui.project_file_picker.sys.platform', 'darwin'),
            patch('ui.project_file_picker.subprocess.run', return_value=CompletedProcess([], 0, json.dumps(''))),
        ):
            self.page.first_file_selection()
        self.assertIsNone(self.page.df)
        self.assertFalse(hasattr(self.page, 'views'))
        self.assertTrue(dpg.get_item_children('Landing Page', 1))

    def test_native_cancel_destroys_tk_and_keeps_the_recording(self):
        self.assertTrue(self.load(self.path))
        manager = self.page.importer
        with (
            patch('ui.project_file_picker.sys.platform', 'win32'),
            patch('ui.project_file_picker.tk.Tk') as root,
            patch('ui.project_file_picker.filedialog.askopenfilename', return_value=''),
        ):
            self.assertFalse(self.page.select_file_tk())
        root.return_value.destroy.assert_called_once()
        self.assertIs(self.page.importer, manager)

    def test_shared_load_automatically_populates_monitor_without_a_second_picker(self):
        self.assertTrue(self.load(self.path))
        monitor = self.page.views['elec_monitor']
        self.assertIs(monitor.manager, self.page.importer)
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
