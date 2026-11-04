"""Dear PyGui presentation of the independent offline sensor report."""

import csv
from pathlib import Path

import dearpygui.dearpygui as dpg

from core.sensor_monitor.gear_report import gear_label
from core.sensor_monitor.plot_data import finding_range, trace_segments, value_limits
from core.sensor_monitor.run_report import save_run_report
from core.sensor_monitor.service import analyze_loaded_recording, analyze_recording


class MonitorView:
    COLORS = {"review": (245, 192, 92), "no_findings": (128, 209, 172),
              "not_assessed": (178, 190, 205), "not_logged": (145, 157, 171)}
    CONTENT = "sensor_monitor_content"
    DETAIL = "sensor_monitor_detail"
    TABLE = "sensor_monitor_table"
    COLUMN_WEIGHTS = (1.3, 1, 1.5, .85, 2.3)

    def __init__(self, DataManager):
        self.manager = DataManager
        self.report = None
        self.source_path = None  # None follows the project's selected recording.
        self.allow_estimated = False
        self.shifts_expected = None
        self.selected_id = "gear"
        self.finding_index = 0
        self.focus_finding = False
        self.error = ""
        self.export_message = ""
        self._project_token = None
        self._built = False
        self._content_size = None
        self._wrapped_text = {}

    def build(self, parent_tag):
        with dpg.child_window(tag=self.CONTENT, parent=parent_tag, border=False, width=-1, height=-1):
            pass
        self._built = True
        self.refresh()

    def refresh(self):
        """Read the current manager rather than a captured, stale dataframe."""
        token = (self.manager.path, id(self.manager.df))
        if token != self._project_token:
            self._project_token = token
            if self.source_path is None:
                self._analyze()
                return
        if self._built and not dpg.get_item_children(self.CONTENT, 1):
            self._render()

    def _analyze(self):
        self.report = None
        self.error = self.export_message = ""
        self.finding_index = 0
        self.focus_finding = False
        options = dict(allow_estimated=self.allow_estimated, shifts_expected=self.shifts_expected)
        try:
            if self.source_path is not None:
                self.report = analyze_recording(self.source_path, **options)
            elif self.manager.path and self.manager.df is not None:
                self.report = analyze_loaded_recording(self.manager, **options)
        except (OSError, UnicodeError, ValueError, KeyError, TypeError, csv.Error) as error:
            self.error = f"Could not analyze the recording: {error}"
        if self._built:
            self._render()

    def _reanalyze(self, sender=None, app_data=None, user_data=None):
        self._analyze()

    def _set_timing(self, sender, app_data, user_data=None):
        self.allow_estimated = bool(app_data)
        self._analyze()

    def _set_shifts(self, sender, app_data, user_data=None):
        self.shifts_expected = {"Unknown": None, "Yes": True, "No": False}[app_data]
        self._analyze()

    def _use_project(self, sender=None, app_data=None, user_data=None):
        self.source_path = None
        self._project_token = (self.manager.path, id(self.manager.df))
        if not self.manager.path or self.manager.df is None:
            self.report = None
            self.error = "No project recording is loaded. Use Open CSV to review a recording here."
            self._render()
            return
        self._analyze()

    def _open_csv(self, sender=None, app_data=None, user_data=None):
        tag = "sensor_monitor_csv_picker"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        default = Path(self.source_path or self.manager.path).parent if (self.source_path or self.manager.path) else Path(__file__).resolve().parents[2] / "_debugging_files" / "USE_THESE"
        if not default.is_dir():
            default = Path.home()
        with dpg.file_dialog(label="Open sensor recording", tag=tag, width=800, height=500,
                             directory_selector=False, file_count=1,
                             modal=True, default_path=str(default), callback=self._csv_selected,
                             cancel_callback=self._close_dialog):
            dpg.add_file_extension(".csv")
            dpg.add_file_extension(".*")

    def _csv_selected(self, sender, app_data, user_data=None):
        self._close_dialog(sender)
        path = app_data.get("file_path_name")
        if path:
            self.source_path = path
            self._analyze()

    def _export(self, sender=None, app_data=None, user_data=None):
        tag = "sensor_monitor_export_picker"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        with dpg.file_dialog(label="Choose report export folder", tag=tag,
                             directory_selector=True, modal=True, width=800, height=500,
                             default_path=str(Path(self.report["source"]["path"]).parent),
                             callback=self._export_selected, cancel_callback=self._close_dialog):
            pass

    def _export_selected(self, sender, app_data, user_data=None):
        self._close_dialog(sender)
        directory = app_data.get("file_path_name")
        if not directory or self.report is None:
            return
        try:
            paths = save_run_report(self.report, directory=directory)
            self.export_message = f"Saved reports: {paths['json']} and {paths['html'].name}"
        except (OSError, ValueError) as error:
            self.export_message = f"Could not export reports: {error}"
        dpg.set_value("sensor_monitor_export_message", self.export_message)

    @staticmethod
    def _close_dialog(sender, app_data=None, user_data=None):
        if sender is not None and dpg.does_item_exist(sender):
            dpg.hide_item(sender)

    def _body_size(self):
        if self._content_size is not None:
            return self._content_size
        width = dpg.get_viewport_client_width() or dpg.get_viewport_width()
        height = dpg.get_viewport_client_height() or dpg.get_viewport_height()
        return max(1, width - 200), max(1, height - 20)

    def _wrap_width(self):
        return max(240, self._body_size()[0] - 48)

    def _column_width(self, column):
        return max(55, int(self._wrap_width() * self.COLUMN_WEIGHTS[column] / sum(self.COLUMN_WEIGHTS)) - 16)

    def _table_height(self):
        return max(230, min(420, int(self._body_size()[1] * .38)))

    def _plot_height(self):
        return max(260, min(480, int(self._body_size()[1] * .48)))

    def _text(self, text, *, column=None, **kwargs):
        if column is not None:
            kwargs["wrap"] = self._column_width(column)
        item = dpg.add_text(text, **kwargs)
        if column is not None or kwargs.get("wrap") == self._wrap_width():
            self._wrapped_text[item] = column
        return item

    def resize(self, width, height):
        """Resize existing widgets without rerunning analysis or resetting plots."""
        self._content_size = (width, height)
        if not self._built:
            return
        for item, column in list(self._wrapped_text.items()):
            if dpg.does_item_exist(item):
                dpg.configure_item(item, wrap=self._wrap_width() if column is None else self._column_width(column))
            else:
                del self._wrapped_text[item]
        if dpg.does_item_exist(self.TABLE):
            dpg.set_item_height(self.TABLE, self._table_height())
        if dpg.does_item_exist("sensor_monitor_selected_plot"):
            dpg.set_item_height("sensor_monitor_selected_plot", self._plot_height())
        if dpg.does_item_exist("sensor_monitor_finding_selector"):
            dpg.set_item_width("sensor_monitor_finding_selector", max(200, self._wrap_width() - 80))

    @staticmethod
    def _number(value):
        return "Unavailable" if value is None else f"{value:,.4g}"

    def _render(self):
        dpg.delete_item(self.CONTENT, children_only=True)
        self._wrapped_text.clear()
        with dpg.group(parent=self.CONTENT):
            self._text("Sensor Monitor", color=(140, 197, 242))
            self._text("Offline recording review | 8 sensor types / 9 channels")
            has_project = bool(self.manager.path and self.manager.df is not None)
            with dpg.group(horizontal=True):
                if not has_project or self.source_path is not None:
                    dpg.add_button(label="Open CSV", callback=self._open_csv)
                if has_project and self.source_path is not None:
                    dpg.add_button(label="Use project recording", callback=self._use_project)
                dpg.add_button(label="Reanalyze", callback=self._reanalyze)
                dpg.add_button(label="Export HTML + JSON", callback=self._export,
                               enabled=self.report is not None)
            if has_project and self.source_path is None:
                self._text("Using the project recording. Change it with File > Load Project.", wrap=self._wrap_width())
            with dpg.group(horizontal=True):
                dpg.add_combo(["Unknown", "Yes", "No"], label="Shifts expected",
                              default_value={None: "Unknown", True: "Yes", False: "No"}[self.shifts_expected],
                              width=110, callback=self._set_shifts)
                dpg.add_checkbox(label="Estimate time when all timestamps are blank",
                                 default_value=self.allow_estimated, callback=self._set_timing)
            self._text("Estimation requires matching sample-rate/duration metadata and assumes uniform sampling.",
                         color=(167, 179, 194), wrap=self._wrap_width())
            if self.error:
                self._text(self.error, color=(255, 160, 140), wrap=self._wrap_width())
            self._text(self.export_message, tag="sensor_monitor_export_message", wrap=self._wrap_width())
            if self.report is None:
                dpg.add_separator()
                self._text("Open a CSV here or use a loaded project recording to see sensor results.", wrap=self._wrap_width())
                return
            report = self.report
            self._text(f"Source: {report['source']['path']}", wrap=self._wrap_width())
            timing = report["timing"]
            axis = timing["axis"]
            self._text(f"{report['source']['measurement_rows']:,} rows | {timing['basis'].replace('_', ' ')} | "
                         f"{self._number(axis[0])} - {self._number(axis[-1])} {timing['unit']}")
            self._text(timing["note"], color=(245, 192, 92) if timing["basis"] != "recorded" else (167, 179, 194), wrap=self._wrap_width())
            counts = report["summary"]["counts"]
            self._text(f"Review: {counts['review']}   No findings: {counts['no_findings']}   "
                         f"Not assessed: {counts['not_assessed']}   Not logged: {counts['not_logged']}")
            self._text("Only gear checks are implemented. Numeric availability describes data, not sensor health.", wrap=self._wrap_width())
            dpg.add_separator()
            self._text("Run overview | Select a sensor to inspect its trace and assessment")
            with dpg.table(tag=self.TABLE, header_row=True, height=self._table_height(), scrollY=True,
                           scrollX=True, freeze_rows=1, resizable=True, row_background=True,
                           policy=dpg.mvTable_SizingStretchProp, borders_innerH=True):
                for label, weight in zip(["Sensor", "Result", "Whole-run trend", "Numeric data", "Main observation"], self.COLUMN_WEIGHTS):
                    dpg.add_table_column(label=label, init_width_or_weight=weight)
                for sensor in report["sensors"]:
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_selectable(label=sensor["name"], user_data=sensor["id"],
                                               callback=self._select_sensor)
                            self._text(f"{sensor['channel']} | {sensor['unit'] or 'Unit unavailable'}", column=0)
                        with dpg.table_cell():
                            self._text(sensor["status_label"], color=self.COLORS[sensor["status"]])
                            self._text(sensor["assessment_scope"], column=1)
                        with dpg.table_cell():
                            self._plot(sensor, f"sensor_monitor_mini_{sensor['id']}", miniature=True)
                            if sensor["logged"] and sensor["data_summary"]["numeric_samples"]:
                                low, high = value_limits(report, sensor)
                                self._text(f"{self._number(low)} - {self._number(high)} {sensor['unit']}", column=2)
                        with dpg.table_cell():
                            summary = sensor["data_summary"]
                            self._text(f"{summary['numeric_fraction']:.1%}" if summary else "Unavailable")
                            if summary:
                                self._text(f"{summary['numeric_samples']:,}/{summary['total_samples']:,}")
                        with dpg.table_cell():
                            self._text(sensor["main_observation"], column=4)
            with dpg.group(tag=self.DETAIL):
                pass
            self._highlight_selected()
            self._render_detail()

    def _highlight_selected(self):
        for index, sensor in enumerate(self.report["sensors"]):
            dpg.unhighlight_table_row(self.TABLE, index)
            if sensor["id"] == self.selected_id:
                dpg.highlight_table_row(self.TABLE, index, (40, 74, 107, 150))

    def _select_sensor(self, sender, app_data, user_data):
        self.selected_id = user_data
        self.finding_index = 0
        self.focus_finding = False
        self._highlight_selected()
        self._render_detail()

    def _select_finding(self, sender, app_data, user_data=None):
        self.finding_index = self._finding_labels.index(app_data)
        self.focus_finding = True
        self._render_detail()

    def _set_focus(self, sender, app_data, user_data):
        self.focus_finding = user_data
        self._render_detail()

    def _plot(self, sensor, prefix, miniature=False):
        if not sensor["logged"] or not sensor["data_summary"]["numeric_samples"]:
            self._text("No channel data" if not sensor["logged"] else "No numeric readings")
            return
        timing = self.report["timing"]
        axis = timing["axis"]
        low, high = value_limits(self.report, sensor)
        with dpg.plot(tag=prefix, height=54 if miniature else self._plot_height(),
                      width=-1, no_title=True,
                      no_menus=miniature, no_inputs=miniature, no_box_select=miniature,
                      no_mouse_pos=miniature, crosshairs=not miniature):
            if not miniature:
                dpg.add_plot_legend()
            label = "Sample index (0-based)" if timing["basis"] == "sample_index" else f"{timing['basis'].title()} time (s)"
            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="" if miniature else label,
                                     no_tick_labels=miniature, no_tick_marks=miniature,
                                     no_gridlines=miniature)
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="" if miniature else sensor["unit"],
                                     no_tick_labels=miniature, no_tick_marks=miniature,
                                     no_gridlines=miniature)
            for index, (x, y) in enumerate(trace_segments(self.report, sensor)):
                series = dpg.add_scatter_series if len(x) == 1 else dpg.add_stair_series if sensor["plot"] == "step" else dpg.add_line_series
                series(x, y, parent=yaxis, label=sensor["name"] if index == 0 else None)
            if not miniature and sensor["findings"]:
                indices = [item["location"]["activation_sample"] for item in sensor["findings"]]
                dpg.add_scatter_series([axis[index] for index in indices],
                                       [sensor["values"][index] if sensor["values"][index] is not None else high for index in indices],
                                       parent=yaxis, label="Finding activation")
            start, end = 0, len(axis) - 1
            if not miniature and self.focus_finding and sensor["findings"]:
                start, end = finding_range(self.report, sensor["findings"][self.finding_index])
            left, right = axis[start], axis[end]
            dpg.set_axis_limits(xaxis, left, right if right > left else left + 1)
            dpg.set_axis_limits(yaxis, low, high)
        if not miniature:
            self._text("Raw readings; gaps stay empty. Drag to pan, scroll to zoom. Finding markers show activation.",
                         color=(167, 179, 194), wrap=self._wrap_width())

    def _render_detail(self):
        dpg.delete_item(self.DETAIL, children_only=True)
        self._wrapped_text = {item: column for item, column in self._wrapped_text.items() if dpg.does_item_exist(item)}
        sensor = next(item for item in self.report["sensors"] if item["id"] == self.selected_id)
        with dpg.group(parent=self.DETAIL):
            dpg.add_separator()
            self._text(sensor["name"], color=(140, 197, 242))
            self._text(f"{sensor['status_label']} | {sensor['assessment_scope']}", color=self.COLORS[sensor["status"]])
            self._text(sensor["main_observation"], wrap=self._wrap_width())
            if not sensor["logged"]:
                return
            findings = sensor["findings"]
            self._finding_labels = [f"{item['id']}: {item['title']}" for item in findings]
            if len(findings) > 1:
                dpg.add_combo(self._finding_labels, default_value=self._finding_labels[self.finding_index],
                              tag="sensor_monitor_finding_selector", label="Finding",
                              width=max(200, self._wrap_width() - 80), callback=self._select_finding)
            if findings and findings[self.finding_index]["scope"] != "whole_recording":
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Whole run", callback=self._set_focus, user_data=False)
                    dpg.add_button(label="Finding context", callback=self._set_focus, user_data=True)
            self._plot(sensor, "sensor_monitor_selected_plot")
            if findings:
                item = findings[self.finding_index]
                self._text(f"{item['id']} | {item['title']}", color=(245, 192, 92), wrap=self._wrap_width())
                self._text(item["message"], wrap=self._wrap_width())
                self._text(self._location_text(item["location"]), wrap=self._wrap_width())
                self._text(f"Next: {item['suggested_action']}", wrap=self._wrap_width())
                with dpg.collapsing_header(label="Finding evidence"):
                    self._text(f"Rule {item['rule_version']} ({item['rule_status']}) | {item['category']}")
                    with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp):
                        for label in ["Sample", "Time (s)", "Raw gear reading"]:
                            dpg.add_table_column(label=label)
                        for sample in item["evidence"]["sample_window"]:
                            with dpg.table_row():
                                self._text(str(sample["sample_index"]))
                                self._text(self._number(sample["seconds"]))
                                self._text(str(sample["raw_gear"]))
            with dpg.collapsing_header(label="Statistics and check details"):
                data = sensor["data_summary"]
                self._text(f"CSV channel: {sensor['channel']} | {sensor['unit']}")
                self._text(f"Minimum: {self._number(data['minimum'])} | Median: {self._number(data['median'])} | Maximum: {self._number(data['maximum'])}")
                self._text(f"Missing: {data['missing_samples']:,} | Invalid: {data['invalid_samples']:,} | Numeric: {data['numeric_samples']:,}/{data['total_samples']:,}")
                self._text(self.report["timing"]["note"], wrap=self._wrap_width())
                if sensor["analysis"]:
                    analysis = sensor["analysis"]
                    rules = analysis["analysis_settings"]["rules"]
                    self._text(f"Gear rule version: {rules['version']} ({rules['status']})")
                    self._text("Confirmed gears: " + (", ".join(gear_label(code) for code in analysis["data_summary"]["confirmed_gears"]) or "None"))
                    for check in sensor["checks"]:
                        dpg.add_separator()
                        self._text(f"{check['name']} | {check['assessment']} | {check['outcome']}", wrap=self._wrap_width())
                        self._text(check["message"], wrap=self._wrap_width())
                    for note in sensor["notes"]:
                        dpg.add_separator()
                        self._text(f"{note['id']}: {note['title']}", wrap=self._wrap_width())
                        self._text(note["message"], wrap=self._wrap_width())
                        self._text(self._location_text(note["location"]), wrap=self._wrap_width())
                for limitation in sensor["limitations"]:
                    self._text(limitation, bullet=True, wrap=self._wrap_width())
            with dpg.collapsing_header(label="Report scope and limitations"):
                for limitation in self.report["limitations"]:
                    self._text(limitation, bullet=True, wrap=self._wrap_width())

    def _location_text(self, location):
        rows = f"Samples {location['start_sample']} - {location['end_sample']} (0-based)"
        if location["start_seconds"] is None:
            return rows
        return (f"{location['time_basis'].title()} {self._number(location['start_seconds'])} - "
                f"{self._number(location['end_seconds'])} s | Evidence span "
                f"{self._number(location['elapsed_span_seconds'])} s | {rows}")
