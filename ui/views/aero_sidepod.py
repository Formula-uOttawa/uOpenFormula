import dearpygui.dearpygui as dpg
import math


class SidePodView:

    def __init__(self, DataManager):

        self.df = DataManager.df
        self.path = DataManager.path
        self.calibration_values = {}


    def build(self, parent_tag):
        """Called once to populate the window."""

        if self.path == "":

            dpg.add_text("Side Pod Pressure Analysis", parent=parent_tag)
            dpg.add_separator(parent=parent_tag)
            dpg.add_text(
                "Load a file to see data.",
                tag="sidepod_placeholder",
                parent=parent_tag
            )

        else:
            self.refresh()



    def analog_to_pressure(self, value, calibration):
        """Convert a baseline-corrected Arduino analog value to pressure in Pa."""
        return (value - calibration) * 4.89


    def analog_to_airspeed(self, value, calibration):
        """Convert Arduino analog value from pitot sensor to km/h."""

        pressure = self.analog_to_pressure(value, calibration)

        if pressure <= 0:
            return 0

        air_density = 1.225

        speed_ms = math.sqrt((2 * pressure) / air_density)

        return speed_ms * 3.6


    def refresh(self):
        """Called after new data loads to update content."""

        if dpg.does_item_exist("sidepod_placeholder"):
            dpg.delete_item("sidepod_placeholder")


        aero_sensors = ("Aero 1", "Aero 2", "Aero 3")
        if len(self.df) < 5:
            raise ValueError("Side pod analysis needs at least five samples to calibrate its sensors.")

        # The first five samples establish each analog sensor's individual zero.
        self.calibration_values = {
            sensor: self.df[sensor].iloc[:5].mean()
            for sensor in aero_sensors
        }

        self.time = self.df["Time"].tolist()

        # Aero 1 = Front sidepod pressure
        self.front_pressure = [
            self.analog_to_pressure(value, self.calibration_values["Aero 1"])
            for value in self.df["Aero 1"].tolist()
        ]

        # Aero 3 = Rear sidepod pressure
        self.rear_pressure = [
            self.analog_to_pressure(value, self.calibration_values["Aero 3"])
            for value in self.df["Aero 3"].tolist()
        ]

        # Aero 2 = Pitot airspeed
        self.airspeed = [
            self.analog_to_airspeed(value, self.calibration_values["Aero 2"])
            for value in self.df["Aero 2"].tolist()
        ]

        # GPS speed
        self.gps_speed = self.df["GPS Speed"].tolist()


        with dpg.child_window(tag="Side Pod Pressure graph", show=True):

            with dpg.plot(
                label="Side Pod Pressure",
                height=800,
                width=dpg.get_viewport_width() - 250,
                crosshairs=True
            ):

                dpg.add_plot_legend()

                dpg.add_plot_axis(
                    dpg.mvXAxis,
                    label="Time"
                )

                dpg.add_plot_axis(
                    dpg.mvYAxis,
                    label="Pressure (Pa)",
                    tag="Pressure Axis"
                )

                dpg.add_plot_axis(
                    dpg.mvYAxis,
                    label="Speed (km/h)",
                    tag="Speed Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.front_pressure,
                    label="Front Pressure",
                    parent="Pressure Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.rear_pressure,
                    label="Rear Pressure",
                    parent="Pressure Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.gps_speed,
                    label="GPS Speed",
                    parent="Speed Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.airspeed,
                    label="Pitot Airspeed",
                    parent="Speed Axis"
                )
