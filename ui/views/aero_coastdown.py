import dearpygui.dearpygui as dpg
from core.coastdown_analysis import run_coastdown_analysis


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
            callback=self.runanalysis,
            parent=parent_tag
        )

        dpg.add_text(
            "Final downforce equation not calculated yet",
            tag="downforce_equation_text",
            wrap=900, #Max line is 900 pixel
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

    def runanalysis(self):

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

        try: # Try to run analysis function on core If it fails in one of the expected ways, handle the error instead of crashing the app
            result = run_coastdown_analysis(
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
        # handles a real error that stops the calculation


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