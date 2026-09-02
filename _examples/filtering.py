
import numpy as np
import pandas as pd
import dearpygui.dearpygui as dpg
from scipy.signal import butter, filtfilt


fs = 100
duration = 10
t = np.arange(0, duration, 1/fs)

trend = 0.5 * t + 2
high_freq = 1.5 * np.sin(2*np.pi*30*t)
noise = np.random.normal(0, 0.5, size=len(t))

signal = trend + high_freq + noise

df = pd.DataFrame({"t": t, "signal": signal})
mean_signal = df["signal"].mean()
print("Mean of signal:", mean_signal)
print(df.head())

coeffs = np.polyfit(df["t"], df["signal"], 1)
slope, intercept = coeffs
print("Slope:",slope)
print("Intercept:", intercept)
df["trend"] = slope * df["t"] + intercept

def lowpass(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    denominator, numerator = butter(order, normal_cutoff, btype="low")
    return filtfilt(denominator, numerator, data)

df["filtered"] = lowpass(df["signal"], cutoff=5, fs=fs) 

dpg.create_context()
with dpg.window(label="Signal Visualization", width=800, height=600):
    with dpg.plot(label="Signal Plot", height=400, width=780):
        dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
        dpg.add_plot_legend()
        with dpg.plot_axis(dpg.mvYAxis, label="Value", tag="y_axis"):
            dpg.add_line_series(df["t"].tolist(), df["signal"].tolist(), label="Raw Signal",parent="y_axis")
            dpg.add_line_series(df["t"].tolist(), df["trend"].tolist(), label="Trend",parent="y_axis")
            dpg.add_line_series(df["t"].tolist(), df["filtered"].tolist(), label="Filtered Signal",parent="y_axis")
dpg.create_viewport(title="Data Visualization", width=820, height=620)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()