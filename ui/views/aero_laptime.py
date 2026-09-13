from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import dearpygui.dearpygui as dpg

from aero_laptime_comparison.aero_laptime_data import AeroLaptimeData
from aero_laptime_comparison.track_alignment import TrackAlignment


class AeroLaptimeView:
    """DearPyGui view for comparing baseline and aero telemetry files."""

    def __init__(self, _importer=None):
        self.data = AeroLaptimeData()
        self.alignment = None
        self.tag = None
        self.baseline_path = None
        self.aero_path = None
        self.channel_items = []

    def build(self, parent_tag):
        self.tag = parent_tag
        with dpg.group(parent=parent_tag):
            dpg.add_text("Aero lap-time comparison", color=(100, 200, 255))
            dpg.add_text(
                "Load two runs, choose a shared channel, then process by distance."
            )
            dpg.add_separator()
            self._build_file_controls()
            dpg.add_separator()
            self._build_processing_controls()
            dpg.add_separator()
            dpg.add_text("Results", color=(100, 200, 255))
            dpg.add_text(
                "Load both datasets and process them to view the comparison.",
                tag=self._tag("result_status"),
            )
            dpg.add_text("", tag=self._tag("summary"), wrap=900)
            self._build_result_area()

    def _tag(self, name):
        return f"{self.tag}_{name}"

    def _build_file_controls(self):
        with dpg.group(horizontal=True):
            dpg.add_text("Baseline / no aero")
            dpg.add_input_text(tag=self._tag("baseline_path"), width=480)
            dpg.add_button(
                label="Browse",
                callback=lambda: self._browse("baseline"),
            )
            dpg.add_button(
                label="Load",
                callback=lambda: self._load("baseline"),
            )
        dpg.add_text("Not loaded", tag=self._tag("baseline_status"))

        with dpg.group(horizontal=True):
            dpg.add_text("Aero package")
            dpg.add_input_text(tag=self._tag("aero_path"), width=480)
            dpg.add_button(
                label="Browse",
                callback=lambda: self._browse("aero"),
            )
            dpg.add_button(
                label="Load",
                callback=lambda: self._load("aero"),
            )
        dpg.add_text("Not loaded", tag=self._tag("aero_status"))

    def _build_processing_controls(self):
        with dpg.group(horizontal=True):
            dpg.add_text("Latitude")
            dpg.add_combo(
                [],
                tag=self._tag("latitude"),
                width=220,
                enabled=False,
            )
            dpg.add_text("Longitude")
            dpg.add_combo(
                [],
                tag=self._tag("longitude"),
                width=220,
                enabled=False,
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Comparison channel")
            dpg.add_combo(
                [],
                tag=self._tag("channel"),
                width=300,
                enabled=False,
                callback=self._channel_changed,
            )
            dpg.add_text("Interpolation step (m)")
            dpg.add_input_float(
                tag=self._tag("step"),
                default_value=1.0,
                min_value=0.001,
                min_clamped=True,
                width=130,
            )
            dpg.add_button(label="Process", callback=self._process)

        dpg.add_text("Shared channels", tag=self._tag("channel_count"))
        dpg.add_child_window(
            tag=self._tag("channels"),
            width=-1,
            height=90,
            border=True,
        )

    def _build_result_area(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=500, height=360, border=True):
                dpg.add_text("Aligned channel values", color=(100, 200, 255))
                dpg.add_table(
                    tag=self._tag("table"),
                    header_row=True,
                    resizable=True,
                    scrollY=True,
                    borders_innerH=True,
                    borders_innerV=True,
                )
            with dpg.child_window(width=-1, height=360, border=True):
                dpg.add_text("Telemetry over distance", color=(100, 200, 255))
                with dpg.plot(
                    tag=self._tag("plot"),
                    height=-1,
                    width=-1,
                    anti_aliased=True,
                ):
                    dpg.add_plot_axis(
                        dpg.mvXAxis,
                        label="Distance (m)",
                        tag=self._tag("plot_x"),
                    )
                    dpg.add_plot_axis(
                        dpg.mvYAxis,
                        label="Value",
                        tag=self._tag("plot_y"),
                    )

        dpg.add_text("Aero-effect track heatmap", color=(100, 200, 255))
        dpg.add_text(
            "Baseline and aero tracks share the same color scale: blue is lower, red is higher.",
            tag=self._tag("color_range"),
        )
        dpg.add_drawlist(tag=self._tag("drawlist"), width=-1, height=420)

    def _browse(self, dataset):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title=f"Select {dataset} CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        root.destroy()
        if path:
            dpg.set_value(self._tag(f"{dataset}_path"), path)
            self._set_status(f"{dataset}_status", f"Path selected: {Path(path).name}")

    def _load(self, dataset):
        path = dpg.get_value(self._tag(f"{dataset}_path")).strip()
        if not path:
            self._set_status(f"{dataset}_status", "Enter or choose a CSV path first.", error=True)
            return

        try:
            if dataset == "baseline":
                dataframe = self.data.load_baseline(path)
                manager = self.data.baseline_manager
            else:
                dataframe = self.data.load_aero(path)
                manager = self.data.aero_manager
            self._set_status(
                f"{dataset}_status",
                f"Loaded {Path(path).name}: {len(dataframe)} rows, "
                f"{len(dataframe.columns)} channels.",
            )
            dpg.set_value(self._tag("result_status"), "Dataset loaded successfully.")
            self._refresh_controls()
        except Exception as error:
            self._set_status(f"{dataset}_status", f"Load failed: {error}", error=True)

    def _refresh_controls(self):
        if not self.data.is_ready():
            return

        columns = self.data.get_common_channels()
        preferred_latitude = "GPS Latitude" if "GPS Latitude" in columns else "GPS_Lat"
        preferred_longitude = "GPS Longitude" if "GPS Longitude" in columns else "GPS_Long"
        coordinate_columns = [column for column in columns if column not in {"Time"}]
        latitude = preferred_latitude if preferred_latitude in coordinate_columns else coordinate_columns[0]
        longitude = preferred_longitude if preferred_longitude in coordinate_columns else coordinate_columns[0]
        comparison_columns = [column for column in columns if column not in {"Time", latitude, longitude}]

        self._set_combo("latitude", coordinate_columns, latitude)
        self._set_combo("longitude", coordinate_columns, longitude)
        self._set_combo("channel", comparison_columns, comparison_columns[0] if comparison_columns else None)
        dpg.configure_item(self._tag("latitude"), enabled=bool(coordinate_columns))
        dpg.configure_item(self._tag("longitude"), enabled=bool(coordinate_columns))
        dpg.configure_item(self._tag("channel"), enabled=bool(comparison_columns))
        dpg.set_value(self._tag("channel_count"), f"Shared channels: {len(columns)}")
        dpg.delete_item(self._tag("channels"), children_only=True)
        for channel in columns:
            dpg.add_text(channel, parent=self._tag("channels"))

    def _set_combo(self, name, items, value):
        dpg.configure_item(self._tag(name), items=items)
        dpg.set_value(self._tag(name), value if value is not None else "")

    def _process(self, _sender=None, _app_data=None):
        if not self.data.is_ready():
            dpg.set_value(self._tag("result_status"), "Load both datasets before processing.")
            return

        channel = dpg.get_value(self._tag("channel"))
        latitude = dpg.get_value(self._tag("latitude"))
        longitude = dpg.get_value(self._tag("longitude"))
        step = dpg.get_value(self._tag("step"))
        try:
            self.data.set_selected_channel(channel)
            self.alignment = TrackAlignment(
                self.data.baseline_df,
                self.data.aero_df,
                lat_column=latitude,
                lon_column=longitude,
                selected_channel=channel,
            )
            self.alignment.process(interpolation_step=step)
            self._render_results(step)
            dpg.set_value(self._tag("result_status"), "Processing complete.")
        except Exception as error:
            dpg.set_value(self._tag("result_status"), f"Processing failed: {error}")

    def _channel_changed(self, _sender, channel):
        if self.alignment is not None and channel:
            self._process()

    def _render_results(self, step):
        summary = self.data.get_summary()
        alignment_info = self.alignment.get_aero_start_alignment()
        color_range = self.alignment.get_color_range()
        dpg.set_value(
            self._tag("summary"),
            f"Baseline: {summary['baseline_rows']} rows | Aero: {summary['aero_rows']} rows | "
            f"Shared channels: {summary['common_channels']}\n"
            f"Aligned points: {len(self.alignment.get_aligned_data())} | Step: {step:g} m | "
            f"Aero start offset: {alignment_info['aero_start_offset_m']:.3f} m",
        )
        dpg.set_value(
            self._tag("color_range"),
            f"Aero-effect range: {color_range['min']:.3f} to {color_range['max']:.3f} "
            f"for {color_range['channel']}",
        )
        self._render_table()
        self._render_plot()
        self._render_heatmap()

    def _render_table(self):
        aligned = self.alignment.get_aligned_data()
        channel = self.alignment.selected_channel
        table = self._tag("table")
        dpg.delete_item(table, children_only=True)
        for label in ["Distance (m)", "Baseline", "Aero", "Delta"]:
            dpg.add_table_column(label=label, parent=table)
        columns = [
            "distance",
            f"baseline_{channel}",
            f"aero_{channel}",
            f"delta_{channel}",
        ]
        for _, row in aligned.iloc[::max(1, len(aligned) // 100)].iterrows():
            with dpg.table_row(parent=table):
                for column in columns:
                    dpg.add_text(f"{row[column]:.4f}")

    def _render_plot(self):
        aligned = self.alignment.get_aligned_data()
        channel = self.alignment.selected_channel
        x = aligned["distance"].tolist()
        dpg.delete_item(self._tag("plot_y"), children_only=True)
        dpg.add_line_series(x, aligned[f"baseline_{channel}"].tolist(), label="Baseline", parent=self._tag("plot_y"))
        dpg.add_line_series(x, aligned[f"aero_{channel}"].tolist(), label="Aero", parent=self._tag("plot_y"))
        dpg.add_line_series(x, aligned[f"delta_{channel}"].tolist(), label="Delta", parent=self._tag("plot_y"))
        dpg.fit_axis_data(self._tag("plot_x"))
        dpg.fit_axis_data(self._tag("plot_y"))

    def _render_heatmap(self):
        drawlist = self._tag("drawlist")
        dpg.delete_item(drawlist, children_only=True)
        tracks = self.alignment.get_track_points()
        all_x = [value for track in tracks.values() for value in track["x"]]
        all_y = [value for track in tracks.values() for value in track["y"]]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        span = max(max_x - min_x, max_y - min_y) or 1.0
        width, height, margin = 900, 420, 20

        def point(x_value, y_value):
            return [
                margin + (x_value - min_x) / span * (width - 2 * margin),
                height - margin - (y_value - min_y) / span * (height - 2 * margin),
            ]

        for track_name, track in tracks.items():
            points = track[["x", "y"]].to_numpy()
            colors = track["heatmap_color"].tolist()
            for index in range(len(points) - 1):
                dpg.draw_line(
                    point(*points[index]),
                    point(*points[index + 1]),
                    color=(*colors[index], 255),
                    thickness=3,
                    parent=drawlist,
                )
        dpg.draw_text([margin, margin], "Baseline + Aero", color=(255, 255, 255, 255), parent=drawlist)

    def _set_status(self, tag_name, message, error=False):
        dpg.set_value(self._tag(tag_name), message)
        dpg.configure_item(
            self._tag(tag_name),
            color=(255, 120, 120) if error else (180, 255, 180),
        )