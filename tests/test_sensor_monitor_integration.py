import copy
import csv
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from contextlib import redirect_stdout

import dearpygui.dearpygui as dpg

from core.data_manager import DataManager
from core.sensor_monitor.gear_report import analyze_gear
from core.sensor_monitor.gear_rules import load_gear_rules
from core.sensor_monitor.plot_data import finding_range, trace_segments, value_limits
from core.sensor_monitor.run_report import build_run_report
from core.sensor_monitor.service import analyze_loaded_recording, analyze_run
from core.sensor_monitor.timing import build_timing
from tests.sensor_monitor.test_gear_report import make_run
from tests.sensor_monitor.test_run_report import add_channel
from ui.home_page import HomePage, VIEW_MAP
from ui.views.elec_monitor import MonitorView


def stable_result(value):
    if isinstance(value, dict):
        return {key: stable_result(item) for key, item in value.items() if key != "generated_at"}
    if isinstance(value, list):
        return [stable_result(item) for item in value]
    return value


def write_recording(directory, values, times=None, signals=()):
    run = make_run(values, times=times)
    for name, unit, readings in signals:
        add_channel(run, name, unit, readings)
    path = Path(directory) / 'recording.csv'
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
        writer.writerows(run['metadata'].items())
        writer.writerow(run['channels'])
        writer.writerow([run['units'][channel] for channel in run['channels']])
        writer.writerows([row[channel] for channel in run['channels']] for row in run['data'])
    return path


class SensorServiceTests(unittest.TestCase):
    def test_service_matches_original_report_pipeline_and_does_not_change_input(self):
        run = make_run([1] * 11 + [4] * 11)
        original = copy.deepcopy(run)
        expected = build_run_report(run, build_timing(run), analyze_gear(run, build_timing(run), load_gear_rules()))
        actual = analyze_run(run)
        self.assertEqual(stable_result(actual), stable_result(expected))
        self.assertEqual(run, original)

    def test_estimated_time_remains_opt_in_and_partial_time_is_not_replaced(self):
        run = make_run([1] * 30, times=[''] * 30)
        self.assertEqual(analyze_run(run)['timing']['basis'], 'sample_index')
        self.assertEqual(analyze_run(run, allow_estimated=True)['timing']['basis'], 'estimated')
        run['data'][0]['Time'] = '0'
        result = analyze_run(run, allow_estimated=True)
        self.assertEqual(result['timing']['basis'], 'sample_index')
        self.assertIn('partially missing', result['timing']['note'])

    def test_manager_adapter_preserves_raw_bad_readings_and_leaves_dataframe_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_recording(directory, [''] + ['bad'] + [1.94] * 21 + [2] * 11)
            frame = object()
            manager = SimpleNamespace(path=str(path), df=frame)
            report = analyze_loaded_recording(manager)
            gear = report['sensors'][0]
            self.assertEqual(gear['data_summary']['missing_samples'], 1)
            self.assertEqual(gear['data_summary']['invalid_samples'], 1)
            self.assertEqual(gear['values'][2], 1.94)
            self.assertTrue(any(item['check_id'] == 'gear_signal_quality' for item in gear['findings']))
            self.assertIs(manager.df, frame)

    def test_empty_manager_has_an_actionable_error(self):
        with self.assertRaisesRegex(ValueError, 'Load a project recording'):
            analyze_loaded_recording(SimpleNamespace(path='', df=None))

    def test_trace_segments_do_not_bridge_invalid_readings_or_timestamp_gaps(self):
        report = {'timing': {'axis': [0, .05, .1, 4, 4.05, 4.1], 'gap_after_sample': [2]}}
        sensor = {'values': [1, None, 2, 3, 4, None]}
        self.assertEqual(trace_segments(report, sensor), [([0], [1]), ([.1], [2]), ([4, 4.05], [3, 4])])

    def test_brake_scales_match_only_for_matching_units(self):
        run = make_run([1, 1])
        add_channel(run, 'Front Brake Pres', 'bar', [2, 3])
        add_channel(run, 'Rear Brake Pres', 'bar', [5, 9])
        report = analyze_run(run)
        front, rear = report['sensors'][1:3]
        low, high = value_limits(report, front)
        self.assertAlmostEqual(low, -.63)
        self.assertAlmostEqual(high, 9.63)
        self.assertEqual((low, high), value_limits(report, rear))
        rear['unit'] = 'psi'
        self.assertNotEqual(value_limits(report, front), value_limits(report, rear))

    def test_finding_context_keeps_boundary_samples(self):
        report = {'timing': {'axis': list(range(100))}}
        self.assertEqual(finding_range(report, {'scope': 'local_event', 'location': {'start_sample': 0, 'end_sample': 2}}), (0, 22))
        self.assertEqual(finding_range(report, {'scope': 'whole_recording'}), (0, 99))


class SensorMonitorViewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = write_recording(self.directory.name, [1] * 11 + [4] * 11)
        self.manager = SimpleNamespace(path='', df=None)
        dpg.create_context()
        dpg.create_viewport(width=1440, height=1000)
        with dpg.window(tag='monitor_test_parent'):
            self.view = MonitorView(self.manager)
            self.view.build('monitor_test_parent')

    def tearDown(self):
        dpg.destroy_context()
        self.directory.cleanup()

    def open_recording(self):
        self.manager.path, self.manager.df = str(self.path), object()
        self.view.refresh()

    def test_existing_navigation_node_discovers_monitor_view(self):
        self.assertIs(VIEW_MAP['elec_monitor'], MonitorView)
        self.assertIsNone(self.view.report)

    def test_empty_monitor_guides_users_to_the_shared_project_picker(self):
        items = dpg.get_all_items()
        labels = [dpg.get_item_label(item) for item in items]
        self.assertNotIn('Open CSV', labels)
        reanalyze = items[labels.index('Reanalyze')]
        self.assertFalse(dpg.get_item_configuration(reanalyze)['enabled'])
        text = [dpg.get_value(item) for item in items if dpg.get_item_type(item) == 'mvAppItemType::mvText']
        self.assertIn('Choose a recording with File > Load Project.', text)

    def test_reanalysis_of_removed_recording_does_not_show_stale_results(self):
        self.open_recording()
        self.path.unlink()
        self.view._reanalyze()
        self.assertIsNone(self.view.report)
        self.assertIn('Could not analyze', self.view.error)

    def test_changed_project_recording_refreshes_without_duplicate_widgets(self):
        self.open_recording()
        first = self.view.report
        write_recording(self.directory.name, [0] * 30)
        self.manager.df = object()
        self.view.refresh()
        self.assertIsNot(self.view.report, first)
        self.assertEqual(self.view.report['source']['measurement_rows'], 30)
        self.assertEqual(len(dpg.get_item_children(self.view.TABLE, 1)), 9)

    def test_view_keeps_missing_channels_unavailable_and_finding_focus_works(self):
        self.open_recording()
        self.view._set_focus(None, None, True)
        self.assertTrue(self.view.focus_finding)
        self.view._select_sensor(None, None, 'iat')
        self.assertFalse(dpg.does_item_exist('sensor_monitor_selected_plot'))
        self.view._select_sensor(None, None, 'gear')
        self.assertTrue(dpg.does_item_exist('sensor_monitor_selected_plot'))

    def test_temperature_finding_shows_source_readings_and_can_focus_plot(self):
        write_recording(self.directory.name, [1] * 24,
                        signals=[('ECU IAT', '°C', [20] * 12 + ['27.250'] + [20] * 11)])
        self.open_recording()
        self.view._select_sensor(None, None, 'iat')
        self.view._set_focus(None, None, True)
        text = [dpg.get_value(item) for item in dpg.get_all_items()
                if dpg.get_item_type(item) == 'mvAppItemType::mvText']
        self.assertIn('27.250', text)
        self.assertIn('Abrupt temperature rise | complete | review', text)

    def test_ui_options_keep_backend_timing_and_run_context_semantics(self):
        write_recording(self.directory.name, [0] * 30, times=[''] * 30)
        self.open_recording()
        self.assertEqual(self.view.report['timing']['basis'], 'sample_index')
        self.view._set_timing(None, True)
        self.assertEqual(self.view.report['timing']['basis'], 'estimated')
        self.view._set_shifts(None, 'No')
        self.assertEqual(self.view.report['sensors'][0]['findings'], [])

    def test_optional_export_saves_the_same_report_without_opening_browser(self):
        self.open_recording()
        self.view._export_selected(None, {'file_path_name': self.directory.name})
        saved = next(Path(self.directory.name).glob('*.json'))
        self.assertEqual(json.loads(saved.read_text()), self.view.report)
        self.assertTrue(list(Path(self.directory.name).glob('*.html')))

    def test_existing_raw_and_oil_views_still_build_with_monitor(self):
        dpg.delete_item('monitor_test_parent')
        sample = Path(__file__).resolve().parents[1] / '_debugging_files/USE_THESE/faran_a_3731.csv'
        manager = DataManager()
        with redirect_stdout(io.StringIO()):
            manager.import_and_validate(str(sample))
        page = HomePage.__new__(HomePage)
        page.importer = manager
        page.show_home()
        self.assertEqual(set(page.views), {'raw_data', 'aero_coastdown', 'power_oilstarv', 'elec_monitor'})
        page._switch_main_view('elec_monitor')
        self.assertTrue(dpg.does_item_exist('Rpm & Oil Pressure graph'))
        self.assertTrue(dpg.does_item_exist('show_data'))


if __name__ == '__main__':
    unittest.main()
