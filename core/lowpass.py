import numpy as np
from scipy.signal import butter, filtfilt


def lowpass(data, cutoff, fs, order=2):
    """
    Simple Butterworth low-pass filter.

    data:
        Noisy sensor data.

    cutoff:
        Cutoff frequency in Hz.
        Smaller cutoff = smoother data.

    fs:
        Sample rate in Hz.
        Example: fs = 100 means 100 samples per second.

    order:
        Filter order.
        2 is simple and safe.
    """

    data_array = np.asarray(data, dtype=float)

    nyquist = fs / 2
    normal_cutoff = cutoff / nyquist

    if normal_cutoff <= 0 or normal_cutoff >= 1:
        raise ValueError(
            f"Invalid cutoff. cutoff must be between 0 and fs/2. "
            f"cutoff={cutoff}, fs={fs}, fs/2={nyquist}"
        )

    b, a = butter(order, normal_cutoff, btype="low", analog=False)

    filtered_data = filtfilt(b, a, data_array)

    return filtered_data