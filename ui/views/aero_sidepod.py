import dearpygui.dearpygui as dpg
import math


class SidePodView:

    def __init__(self, DataManager):

        self.df = DataManager.df
        self.path = DataManager.path
        self.calibration_values = {}
        self.process_noise = 1.0  # Q: how quickly the true value may change
        self.measurement_noise = 25.0  # R: how noisy the sensor readings are


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


    def kalman_filter(self, values):

        estimate = float(values[0])
        uncertainty = self.measurement_noise
        filtered = []

        for value in values:
            value = float(value)
            if not math.isfinite(value):
                filtered.append(estimate)
                continue


            uncertainty += self.process_noise
            gain = uncertainty / (uncertainty + self.measurement_noise)
            estimate += gain * (value - estimate)
            uncertainty *= (1.0 - gain)
            filtered.append(estimate)

        return filtered


    def update_filter(self, sender=None, app_data=None, user_data=None):
        """Recalculate and redraw the graph when Q or R changes."""

        self.process_noise = max(0.0, dpg.get_value("sidepod_kalman_q"))
        self.measurement_noise = max(0.000001, dpg.get_value("sidepod_kalman_r"))

        
        dpg.set_value("sidepod_kalman_q", self.process_noise)
        dpg.set_value("sidepod_kalman_r", self.measurement_noise)

        series = {
            "sidepod_front_series": self.front_pressure,
            "sidepod_rear_series": self.rear_pressure,
            "sidepod_pitot_series": self.airspeed,
        }

        for tag, original_values in series.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, [self.time, self.kalman_filter(original_values)])

    def refresh(self):
        """Called after new data loads to update content."""

        if dpg.does_item_exist("sidepod_placeholder"):
            dpg.delete_item("sidepod_placeholder")


        aero_sensors = ("Aero 1", "Aero 2", "Aero 3")

        # The first five value are averaged to caibrate the 0 for each sensor
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

        
        self.gps_speed = self.df["GPS Speed"].tolist()


        
        if dpg.does_item_exist("Side Pod Pressure graph"):
            dpg.delete_item("Side Pod Pressure graph")

        with dpg.child_window(tag="Side Pod Pressure graph"):

            dpg.add_text("Kalman Filter Settings")
            dpg.add_input_float(
                label="Process noise (Q)",
                tag="sidepod_kalman_q",
                default_value=self.process_noise,
                min_value=0.0,
                min_clamped=True,
                format="%.4f",
                callback=self.update_filter
            )
            dpg.add_input_float(
                label="Measurement noise (R)",
                tag="sidepod_kalman_r",
                default_value=self.measurement_noise,
                min_value=0.000001,
                min_clamped=True,
                format="%.4f",
                callback=self.update_filter
            )
            dpg.add_text("Higher Q = responds faster; higher R = smoother but slower.")

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
                    y=self.kalman_filter(self.front_pressure),
                    tag="sidepod_front_series",
                    label="Front Pressure (filtered)",
                    parent="Pressure Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.kalman_filter(self.rear_pressure),
                    tag="sidepod_rear_series",
                    label="Rear Pressure (filtered)",
                    parent="Pressure Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.gps_speed,
                    tag="sidepod_gps_series",
                    label="GPS Speed (filtered)",
                    parent="Speed Axis"
                )

                dpg.add_line_series(
                    x=self.time,
                    y=self.kalman_filter(self.airspeed),
                    tag="sidepod_pitot_series",
                    label="Pitot Airspeed (filtered)",
                    parent="Speed Axis"
                )
