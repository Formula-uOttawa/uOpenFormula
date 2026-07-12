import numpy as np
from scipy.optimize import curve_fit

from core.lowpass import lowpass


def quadratic_model(x, a, b, c):
    return a * x**2 + b * x + c


def run_coastdown_analysis(myData):
    """
    Calculate coastdown/downforce data.
    This function does NOT use matplotlib.
    It only returns data for the DearPyGui view to plot.
    """

    cutoff = 0.5
    fs = 100
    k = 78.81

    required_columns = [
        "Time",
        "GPS Speed",
        "RR Shock Pos",
        "FR Shock Pos",
        "FL Shock Pos",
        "RL Shock Pos",
    ]

    for column in required_columns:
        if column not in myData.columns:
            raise ValueError(f"Missing column: {column}")

    myData = myData.dropna()

    time = myData["Time"].to_numpy(dtype=float)
    speed = myData["GPS Speed"].to_numpy(dtype=float)

    rr_raw = myData["RR Shock Pos"].to_numpy(dtype=float)
    fr_raw = myData["FR Shock Pos"].to_numpy(dtype=float)
    fl_raw = myData["FL Shock Pos"].to_numpy(dtype=float)
    rl_raw = myData["RL Shock Pos"].to_numpy(dtype=float)

    filtered_rr = lowpass(rr_raw, cutoff, fs)
    filtered_fr = lowpass(fr_raw, cutoff, fs)
    filtered_fl = lowpass(fl_raw, cutoff, fs)
    filtered_rl = lowpass(rl_raw, cutoff, fs)

    downforce = -(filtered_rr + filtered_fr + filtered_fl + filtered_rl) * k

    popt, pcov = curve_fit(quadratic_model, speed, downforce)

    a, b, c = popt

    speed_fit = np.linspace(speed.min(), speed.max(), 100)
    downforce_fit = quadratic_model(speed_fit, a, b, c)

    result = {
        "time": time.tolist(),
        "rr_raw": rr_raw.tolist(),
        "rr_filtered": filtered_rr.tolist(),

        "speed": speed.tolist(),
        "downforce": downforce.tolist(),

        "speed_fit": speed_fit.tolist(),
        "downforce_fit": downforce_fit.tolist(),

        "equation": f"y = {a:.4f}x² + {b:.4f}x + {c:.4f}",
    }

    return result