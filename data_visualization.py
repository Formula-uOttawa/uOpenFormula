import numpy as np
import dearpygui.dearpygui as dpg
import matplotlib
matplotlib.use("Agg")  # Offscreen backend, no GUI window
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from tkinter import filedialog
import tkinter as tk


class DataVisualization:
    """Handles all plot rendering (DearPyGui live view) and saving (Matplotlib offscreen)."""

    def __init__(self, data_manager):
        """
        Args:
            data_manager (DataManager): A fully loaded DataManager instance.
        """
        self.dm = data_manager
        self._plot_state = {}  # Stores last render settings for use by save_matplotlib()

    # ------------------------------------------------------------------
    # Filtering & Processing
    # ------------------------------------------------------------------

    def apply_lowpass_filter(self, data, cutoff, fs, order=4):
        """Apply a Butterworth low-pass filter to a data array.

        Args:
            data (array-like): Input signal.
            cutoff (float): Cutoff frequency in Hz.
            fs (float): Sampling frequency in Hz.
            order (int): Filter order.

        Returns:
            np.ndarray: Filtered signal.
        """
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype="low")
        return filtfilt(b, a, data)

    def apply_highpass_filter(self, data, cutoff, fs, order=4):
        """Apply a Butterworth high-pass filter to a data array."""
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype="high")
        return filtfilt(b, a, data)

    def apply_bandpass_filter(self, data, lowcut, highcut, fs, order=4):
        """Apply a Butterworth band-pass filter to a data array."""
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype="band")
        return filtfilt(b, a, data)

    def compute_trend(self, col):
        """Fit a linear trend to a channel column.

        Args:
            col (str): Column name in DataManager.df.

        Returns:
            np.ndarray: Trend values aligned to the Time axis.
        """
        t = self.dm.df["Time"].to_numpy()
        y = self.dm.df[col].to_numpy()
        coeffs = np.polyfit(t, y, 1)
        return np.polyval(coeffs, t)

    # ------------------------------------------------------------------
    # DearPyGui Live Plot
    # ------------------------------------------------------------------

    def render_dpg_plot(self, parent_tag, x_col, y_cols, filter_type="None",
                        cutoff=5.0, fs=100.0, show_trend=False):
        """Build a DearPyGui line plot inside an existing window/group.

        Args:
            parent_tag (str): DPG tag of the parent container.
            x_col (str): Column to use as the X axis (usually "Time").
            y_cols (list[str]): Columns to plot on the Y axis.
            filter_type (str): One of "Low-Pass", "High-Pass", "Band-Pass", "None".
            cutoff (float): Filter cutoff frequency (Hz). For band-pass, this is the low cutoff.
            fs (float): Sampling frequency (Hz).
            show_trend (bool): Whether to overlay a linear trend line.
        """
        df = self.dm.df
        x = df[x_col].tolist()

        # Save state so save_matplotlib() can reproduce the same plot
        self._plot_state = {
            "x_col": x_col,
            "y_cols": y_cols,
            "filter_type": filter_type,
            "cutoff": cutoff,
            "fs": fs,
            "show_trend": show_trend,
        }

        plot_tag = f"plot__{parent_tag}"
        y_axis_tag = f"y_axis__{parent_tag}"

        with dpg.plot(label="Signal Plot", height=-1, width=-1,
                      tag=plot_tag, parent=parent_tag):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label=x_col)

            with dpg.plot_axis(dpg.mvYAxis, label="Value", tag=y_axis_tag):
                for col in y_cols:
                    raw = df[col].to_numpy()

                    # Apply selected filter
                    if filter_type == "Low-Pass":
                        y = self.apply_lowpass_filter(raw, cutoff, fs)
                    elif filter_type == "High-Pass":
                        y = self.apply_highpass_filter(raw, cutoff, fs)
                    elif filter_type == "Band-Pass":
                        y = self.apply_bandpass_filter(raw, cutoff, cutoff * 2, fs)
                    else:
                        y = raw

                    dpg.add_line_series(x, y.tolist(), label=col, parent=y_axis_tag)

                    if show_trend:
                        trend = self.compute_trend(col)
                        dpg.add_line_series(x, trend.tolist(),
                                            label=f"{col} (trend)", parent=y_axis_tag)

    # ------------------------------------------------------------------
    # Matplotlib Offscreen Save
    # ------------------------------------------------------------------

    def save_matplotlib(self, file_path=None):
        """Re-render the last DPG plot via Matplotlib and save to disk.

        Prompts the user for a save path if file_path is not provided.

        Args:
            file_path (str, optional): Full output path including extension.
                                       Supported formats: .png, .pdf, .svg
        """
        if not self._plot_state:
            print("[WARN] No plot has been rendered yet. Call render_dpg_plot() first.")
            return

        if file_path is None:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.asksaveasfilename(
                title="Save Graph",
                defaultextension=".png",
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("PDF Document", "*.pdf"),
                    ("SVG Vector", "*.svg"),
                ],
            )
            root.destroy()

        if not file_path:
            return  # User cancelled

        state = self._plot_state
        df = self.dm.df
        x = df[state["x_col"]].to_numpy()

        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

        for col in state["y_cols"]:
            raw = df[col].to_numpy()

            if state["filter_type"] == "Low-Pass":
                y = self.apply_lowpass_filter(raw, state["cutoff"], state["fs"])
            elif state["filter_type"] == "High-Pass":
                y = self.apply_highpass_filter(raw, state["cutoff"], state["fs"])
            elif state["filter_type"] == "Band-Pass":
                y = self.apply_bandpass_filter(raw, state["cutoff"], state["cutoff"] * 2, state["fs"])
            else:
                y = raw

            ax.plot(x, y, label=col, linewidth=1.2)

            if state["show_trend"]:
                trend = self.compute_trend(col)
                ax.plot(x, trend, linestyle="--", linewidth=1.0, label=f"{col} (trend)")

        ax.set_xlabel(state["x_col"])
        ax.set_ylabel("Value")
        ax.set_title(f"Formula uOttawa — {', '.join(state['y_cols'])}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(file_path)
        plt.close(fig)
        print(f"[INFO] Graph saved to: {file_path}")
