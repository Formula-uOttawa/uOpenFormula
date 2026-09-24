from __future__ import annotations

import dearpygui.dearpygui as dpg
from core.coastdown_analysis import run_downforce_analysis, run_aero_drag_analysis
from core.data_manager import DataManager


class AeroCoastdownView:

    def __init__(self, data_manager: DataManager): # give it a data_manager object, and save that object inside the class as self.dm
        self.dm = data_manager

    def build(self, parent_tag: str | int) -> None:

        dpg.add_spacer(
            height=10,
            parent=parent_tag
        )

        dpg.add_text(
            "Coastdown Analysis",
            parent=parent_tag
        )

        dpg.add_spacer(
            height=15,
            parent=parent_tag
        )

        dpg.add_input_float(
            label="Car + driver mass (kg)",
            tag="coastdown_mass",
            default_value=0,
            width=180,
            format="%.2f",
            parent=parent_tag,
        )

        dpg.add_input_double(
            label="What time did the CoastDown run start?",
            tag="coastdown_time_start",
            default_value=0,
            width=180,
            format="%.2f",
            parent=parent_tag,
        )

        dpg.add_input_double(
            label="What time did the CoastDown run end?",
            tag="coastdown_time_end",
            default_value=0,
            width=180,
            format="%.6f",
            parent=parent_tag,
        )

        dpg.add_input_double(
            label="Reference point for RR Shock Pos (mm)",
            tag="Pot_RR_Reference",
            default_value=0,
            width=180,
            format="%.6f",
            parent=parent_tag,
        )

        dpg.add_input_double(
            label="Reference point for FR Shock Pos (mm)",
            tag="Pot_FR_Reference",
            default_value=0,
            width=180,
            format="%.6f",
            parent=parent_tag,
        )

        dpg.add_input_double(
            label="Reference point for FL Shock Pos (mm)",
            tag="Pot_FL_Reference",
            default_value=0,
            width=180,
            format="%.6f",
            parent=parent_tag,
        )

        dpg.add_input_double(
            label="Reference point for RL Shock Pos (mm)",
            tag="Pot_RL_Reference",
            default_value=0,
            width=180,
            format="%.6f",
            parent=parent_tag,
        )

        dpg.add_button(
            label="Run Analysis",
            tag="run_coastdown_button",
            width=280,
            height=40,
            callback=self.run_analysis,
            parent=parent_tag
        )

        dpg.add_text(
            "Final downforce equation not calculated yet",
            tag="downforce_equation_text",
            wrap=900,
            parent=parent_tag
        )

        dpg.add_child_window(
            tag="coastdown_plot_area",
            width=-1,
            height=350,
            parent=parent_tag,
        )

        with dpg.plot(
            label="Estimated downforce",
            height=300,
            width=-1,
            parent="coastdown_plot_area",
        ):

            dpg.add_plot_axis(
                dpg.mvXAxis,
                label="Speed (km/h)",
                tag="downforce_x"
            )

            dpg.add_plot_axis(
                dpg.mvYAxis,
                label="Estimated downforce (N)",
                tag="downforce_y"
            )

            dpg.add_line_series(
                [], [],
                label="Low-pass data",
                tag="downforce_data",
                parent="downforce_y",
            )

            dpg.add_line_series(
                [], [],
                label="Fit",
                tag="downforce_fit",
                parent="downforce_y",
            )

        dpg.add_spacer(height=10, parent=parent_tag)

        dpg.add_text(
            "Final drag force equation not calculated yet",
            tag="drag_equation_text",
            wrap=900,
            parent=parent_tag
        )

        with dpg.tooltip("drag_equation_text"):
            dpg.add_text(
                "Estimated aero drag = K * v^2, with v in m/s.\n"
                "K = 0.5 * air density * Cd * frontal area, in kg/m.\n"
            )

        dpg.add_child_window(
            tag="drag_plot_area",
            width=-1,
            height=350,
            parent=parent_tag,
        )

        with dpg.plot(
            label="Estimated aerodynamic drag",
            height=300,
            width=-1,
            parent="drag_plot_area",
        ):
            dpg.add_plot_axis(
                dpg.mvXAxis,
                label="Speed (km/h)",
                tag="drag_x"
            )
            dpg.add_plot_axis(
                dpg.mvYAxis,
                label="Estimated drag force (N)",
                tag="drag_y"
            )
            dpg.add_line_series(
                [], [],
                label="Fit",
                tag="drag_fit",
                parent="drag_y",
            )

    def run_analysis(self):
        self.analyze_downforce()
        self.analyze_aero_drag()

    def analyze_downforce(self):

        dpg.set_value("downforce_data", [[], []])
        dpg.set_value("downforce_fit", [[], []])
        dpg.set_value("downforce_equation_text", "")
        # clears the old result from CSV1 before calculating CSV2

        time_start = dpg.get_value("coastdown_time_start")
        time_end = dpg.get_value("coastdown_time_end")
        rr_reference = dpg.get_value("Pot_RR_Reference")
        fr_reference = dpg.get_value("Pot_FR_Reference")
        fl_reference = dpg.get_value("Pot_FL_Reference")
        rl_reference = dpg.get_value("Pot_RL_Reference")

        try: 
            result = run_downforce_analysis(
                self.dm.df,
                time_start,
                time_end,
                rr_reference,
                fr_reference,
                fl_reference,
                rl_reference,
            )
        except (ValueError, RuntimeError) as error: #skip this line if try passed
            dpg.set_value("downforce_equation_text", str(error))
            return

        dpg.set_value(
            "downforce_data",
            [result["speed"], result["downforce"]]
        )

        dpg.set_value(
            "downforce_fit",
            [result["speed_fit"], result["downforce_fit"]]
        )

        message = f"Estimated fit: {result['equation']} (v in km/h)."

        dpg.set_value("downforce_equation_text", message)
        dpg.fit_axis_data("downforce_x")
        dpg.fit_axis_data("downforce_y")

    def analyze_aero_drag(self):
        dpg.set_value("drag_fit", [[], []])
        dpg.set_value("drag_equation_text", "")
        mass = dpg.get_value("coastdown_mass")
        time_start = dpg.get_value("coastdown_time_start")
        time_end = dpg.get_value("coastdown_time_end")

        try:
            result = run_aero_drag_analysis(self.dm.df, time_start, time_end, mass)
        except (ValueError, RuntimeError) as error:
            dpg.set_value("drag_equation_text", str(error))
            return

        if result["K"] is None:
            dpg.set_value("drag_equation_text", "Drag unavailable")
            return

        dpg.set_value("drag_fit", [result["speed_fit"], result["drag_fit"]])
        message = (
            f"Estimated aero drag: {result['equation']} (N, v in km/h). "
            f"K = {result['K']:.6f} kg/m"
            " | F_drag = (1/2) * rho * Cd * A * v² (v in m/s)"
        )
        dpg.set_value("drag_equation_text", message)
        dpg.fit_axis_data("drag_x")
        dpg.fit_axis_data("drag_y")
