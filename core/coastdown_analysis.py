import numpy as np
from scipy.optimize import curve_fit

from core.lowpass import lowpass


def quadratic_model(x, a, b, c):
    return a * x**2 + b * x + c

def _prepare_data(myData, time_start, time_end, required_columns):

    for column in required_columns:
        if column not in myData.columns:
            raise ValueError(f"Missing column: {column}")

    myData = myData[required_columns]
    myData = myData.dropna()
    myData = myData[myData["Time"].between(time_start, time_end)]
    time = myData["Time"].to_numpy(dtype=float)
    speed = myData["GPS Speed"].to_numpy(dtype=float)

    time_steps = np.diff(time) #sensor warning similar
    if np.any(time_steps <= 0):
        raise ValueError("Time values must increase without duplicates.")
    if np.unique(speed).size < 3:
        raise ValueError("At least 3 different speeds are needed for the fit.")
    return myData

def run_downforce_analysis(
    myData, time_start, time_end,
    rr_reference, fr_reference, fl_reference, rl_reference,
    ):
    
    required_columns = ["Time", "GPS Speed", "RR Shock Pos", "FR Shock Pos", "FL Shock Pos", "RL Shock Pos",]
    myData = _prepare_data(myData, time_start, time_end, required_columns)
    time = myData["Time"].to_numpy(dtype=float)
    speed = myData["GPS Speed"].to_numpy(dtype=float)
    cutoff = 0.5
    fs = 1 / np.median(np.diff(time))  # Use the RS3 CSV sample rate
    k = 78.81 

    rr_raw = myData["RR Shock Pos"].to_numpy(dtype=float)
    fr_raw = myData["FR Shock Pos"].to_numpy(dtype=float)
    fl_raw = myData["FL Shock Pos"].to_numpy(dtype=float)
    rl_raw = myData["RL Shock Pos"].to_numpy(dtype=float)

    filtered_rr = lowpass(rr_raw, cutoff, fs)
    filtered_fr = lowpass(fr_raw, cutoff, fs)
    filtered_fl = lowpass(fl_raw, cutoff, fs)
    filtered_rl = lowpass(rl_raw, cutoff, fs)

    downforce = -(
        (filtered_rr - rr_reference)
        + (filtered_fr - fr_reference)
        + (filtered_fl - fl_reference)
        + (filtered_rl - rl_reference)
    ) * k

    popt, pcov = curve_fit(quadratic_model, speed, downforce)

    a, b, c = popt

    speed_fit = np.linspace(speed.min(), speed.max(), 100)
    downforce_fit = quadratic_model(speed_fit, a, b, c)

    return {
        "time": time.tolist(),
        "rr_raw": rr_raw.tolist(),
        "rr_filtered": filtered_rr.tolist(),
        "speed": speed.tolist(),
        "downforce": downforce.tolist(),
        "speed_fit": speed_fit.tolist(),
        "downforce_fit": downforce_fit.tolist(),
        "equation": f"y = {a:.4f}x² + {b:.4f}x + {c:.4f}",
    }

def run_aero_drag_analysis(myData, time_start, time_end, mass):
    required_columns = ["Time", "GPS Speed", "GPS Slope"]
    myData = _prepare_data(myData, time_start, time_end, required_columns)
    time = myData["Time"].to_numpy(dtype=float)
    speed = myData["GPS Speed"].to_numpy(dtype=float)

    # 1. Convert speed to m/s.
    speed_mps = speed / 3.6

    # 2. Calculate acceleration from speed and time a = dv/dt.
    acceleration = np.gradient(speed_mps, time)

    # 3. Calculate total resisting force: F = -m * a.
    total_resistive_force = -mass * acceleration

    # 4. Subtract the force from the road slope: F_slope = m * g * sin(angle).
    slope_degrees = myData["GPS Slope"].to_numpy(dtype=float)
    slope_radians = np.deg2rad(slope_degrees)
    gravity = 9.81
    slope_force = mass * gravity * np.sin(slope_radians) #Fslop=mgsin()
    total_resistive_force = total_resistive_force - slope_force

    # 5. Fit total resistance = K * v^2 + b * v + c.
    resistance_fit, _ = curve_fit(quadratic_model, speed_mps, total_resistive_force)

    # 6. K = 0.5 * rho * Cd * A, in kg/m.
    # rho = air density, Cd = drag coefficient, A = frontal area.
    # This fit estimates their combined factor; it cannot find them separately.
    # Treating the v^2 term as aero requires the assumptions in the docstring.
    K = resistance_fit[0]

    if not np.isfinite(K) or K <= 0: #sensor warning exmp
        return {"K": None, "speed_fit": [], "drag_fit": []}

    # 7. Calculate the estimated drag curve in N, using speed in m/s.
    speed_fit = np.linspace(speed.min(), speed.max(), 100)
    speed_fit_mps = speed_fit / 3.6
    speed_squared = speed_fit_mps**2
    drag_fit = K * speed_squared # because K=1/2*p*Cd*A and Fdrag=*1/2*p*Cd*Av^2 so Fdrag=Kv^2

    # 8. Display the equation with speed in km/h to match the plot axis.
    equation_coefficient = K / 3.6**2
    return {
        "K": float(K),
        "speed_fit": speed_fit.tolist(),
        "drag_fit": drag_fit.tolist(),
        "equation": f"F = {equation_coefficient:.6f}v²",
        }