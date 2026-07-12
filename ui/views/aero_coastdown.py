import dearpygui.dearpygui as dpg

from core.coastdown_analysis import run_coastdown_analysis


class AeroCoastdownView:

    def __init__(self, DataManager):
        self.dm = DataManager

    def build(self, parent_tag):
        """Called once to populate the window."""

        self.parent_tag = parent_tag

        dpg.add_text("Coastdown Analysis", parent=parent_tag)
        dpg.add_separator(parent=parent_tag)

        dpg.add_text(
            "Load a CSV file first.",
            tag="coastdown_message",
            parent=parent_tag
        )

        dpg.add_button(
            label="Refresh Coastdown View",
            callback=self.refresh,
            parent=parent_tag
        )

        dpg.add_button(
            label="Run Coastdown Analysis",
            callback=self.run_coastdown_analysis,
            parent=parent_tag
        )

        dpg.add_separator(parent=parent_tag)

        dpg.add_text(
            "",
            tag="coastdown_result",
            parent=parent_tag
        )

        dpg.add_child_window(
            tag="coastdown_plot_area",
            parent=parent_tag,
            height=600,
            width=-1,
            border=True
        )

    def refresh(self):
        """Called after new data loads to update content."""

        if self.dm.df is None:
            dpg.set_value("coastdown_message", "No data loaded yet.")
            dpg.set_value("coastdown_result", "")
            return

        df = self.dm.df

        dpg.set_value(
            "coastdown_message",
            "Data loaded successfully."
        )

        result_text = (
            f"Rows: {len(df)}\n"
            f"Columns: {list(df.columns)}"
        )

        dpg.set_value("coastdown_result", result_text)

    def run_coastdown_analysis(self):
        """Runs coastdown analysis and plots inside DearPyGui."""

        if self.dm.df is None:
            dpg.set_value(
                "coastdown_result",
                "Error: No data loaded. Load a CSV first."
            )
            return

        try:
            result = run_coastdown_analysis(self.dm.df)

            dpg.set_value(
                "coastdown_result",
                "Coastdown analysis finished.\n"
                f"Quadratic equation: {result['equation']}"
            )

            self.draw_plots(result)

        except Exception as error:
            dpg.set_value(
                "coastdown_result",
                f"Coastdown analysis error:\n{error}"
            )

    def draw_plots(self, result):
        """Draw DearPyGui plots inside the app."""

        # Clear old plots first
        dpg.delete_item("coastdown_plot_area", children_only=True)

        # Plot 1: raw vs filtered shock position
        with dpg.plot(
            label="RR Shock Position: Raw vs Filtered",
            height=250,
            width=-1,
            parent="coastdown_plot_area"
        ):
            dpg.add_plot_legend()

            dpg.add_plot_axis(
                dpg.mvXAxis,
                label="Time [s]",
                tag="shock_x_axis"
            )

            dpg.add_plot_axis(
                dpg.mvYAxis,
                label="Shock Position",
                tag="shock_y_axis"
            )

            dpg.add_line_series(
                result["time"],
                result["rr_raw"],
                label="RR Raw",
                parent="shock_y_axis"
            )

            dpg.add_line_series(
                result["time"],
                result["rr_filtered"],
                label="RR Filtered",
                parent="shock_y_axis"
            )

        # Plot 2: downforce vs speed with curve fit
        with dpg.plot(
            label="Downforce vs GPS Speed",
            height=300,
            width=-1,
            parent="coastdown_plot_area"
        ):
            dpg.add_plot_legend()

            dpg.add_plot_axis(
                dpg.mvXAxis,
                label="GPS Speed",
                tag="downforce_x_axis"
            )

            dpg.add_plot_axis(
                dpg.mvYAxis,
                label="Downforce",
                tag="downforce_y_axis"
            )

            dpg.add_line_series(
                result["speed"],
                result["downforce"],
                label="Filtered Downforce",
                parent="downforce_y_axis"
            )

            dpg.add_line_series(
                result["speed_fit"],
                result["downforce_fit"],
                label="Quadratic Curve Fit",
                parent="downforce_y_axis"
            )