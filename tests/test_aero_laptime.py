from pathlib import Path

import pytest

from aero_laptime_comparison.aero_laptime_data import AeroLaptimeData
from aero_laptime_comparison.track_alignment import TrackAlignment
from core.data_manager import DataManager


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "tests" / "data"
BASELINE_PATH = DATA_DIR / "baseline.csv"
AERO_PATH = DATA_DIR / "aero.csv"


def log_completed(message):
    """Print a terminal message only after the described action succeeds."""
    print(f"[COMPLETED] {message}", flush=True)


def load_csv(path, dataset_name):
    manager = DataManager()
    dataframe = manager.import_and_validate(str(path))
    log_completed(
        f"Loaded and validated the {dataset_name} dataset from {path} "
        f"({len(dataframe)} rows, {len(dataframe.columns)} columns)."
    )
    return manager, dataframe


@pytest.fixture
def loaded_datasets():
    baseline_manager, baseline_df = load_csv(BASELINE_PATH, "baseline")
    aero_manager, aero_df = load_csv(AERO_PATH, "aero")
    return baseline_manager, baseline_df, aero_manager, aero_df


def test_full_aero_laptime_comparison(loaded_datasets):
    (
        baseline_manager,
        baseline_df,
        aero_manager,
        aero_df,
    ) = loaded_datasets

    data = AeroLaptimeData()
    data.baseline_manager = baseline_manager
    data.aero_manager = aero_manager
    data.baseline_df = baseline_df
    data.aero_df = aero_df
    data.baseline_metadata = baseline_manager.metadata
    data.aero_metadata = aero_manager.metadata
    data._update_common_channels()
    log_completed(
        f"Prepared AeroLaptimeData with {len(data.get_common_channels())} "
        "channels shared by both datasets."
    )

    assert data.is_ready()
    log_completed("Confirmed AeroLaptimeData reports both datasets as ready.")

    summary = data.get_summary()
    assert summary["baseline_rows"] == len(baseline_df)
    assert summary["aero_rows"] == len(aero_df)
    assert summary["common_channels"] == len(data.get_common_channels())
    log_completed(f"Checked dataset summary: {summary}.")

    selected_channel = next(
        channel
        for channel in data.get_common_channels()
        if channel not in {"Time", "GPS_Lat", "GPS_Long"}
    )
    data.set_selected_channel(selected_channel)
    assert data.get_selected_channel() == selected_channel
    log_completed(f"Selected shared telemetry channel '{selected_channel}'.")

    alignment = TrackAlignment(
        baseline_df,
        aero_df,
        lat_column="GPS Latitude",
        lon_column="GPS Longitude",
        selected_channel=selected_channel,
    )
    log_completed("Created TrackAlignment with both telemetry datasets.")

    result = alignment.process(interpolation_step=1.0)
    assert result["baseline_track"] is alignment.baseline_track
    assert result["aero_track"] is alignment.aero_track
    assert result["aligned_data"] is alignment.aligned_data
    log_completed(
        "Processed native tracks, aligned track starts, interpolated shared "
        f"channels, and generated {len(alignment.aligned_data)} aligned points."
    )

    track_points = alignment.get_track_points()
    assert set(track_points) == {"baseline", "aero"}
    assert len(track_points["baseline"]) >= 2
    assert len(track_points["aero"]) >= 2
    log_completed("Retrieved and verified native baseline and aero track points.")

    aligned = alignment.get_aligned_data()
    assert len(aligned) >= 2
    assert aligned["distance"].is_monotonic_increasing
    assert f"baseline_{selected_channel}" in aligned
    assert f"aero_{selected_channel}" in aligned
    assert f"delta_{selected_channel}" in aligned
    assert "heatmap_color" in aligned
    log_completed(
        "Verified the common distance axis, interpolated channel values, "
        "selected-channel delta, and aligned heatmap colors."
    )

    comparison = alignment.get_comparison(float(aligned["distance"].iloc[0]))
    assert comparison["baseline"]
    assert comparison["aero"]
    assert comparison["selected_channel"]["channel"] == selected_channel
    assert comparison["selected_channel"]["delta"] == pytest.approx(
        comparison["selected_channel"]["aero"]
        - comparison["selected_channel"]["baseline"]
    )
    log_completed(
        f"Compared both datasets at aligned distance "
        f"{comparison['actual_distance']:.3f} m."
    )

    color_range = alignment.get_color_range()
    assert color_range["channel"] == selected_channel
    assert color_range["min"] <= 0 <= color_range["max"]
    assert color_range["min"] == pytest.approx(-color_range["max"])
    assert all(
        isinstance(color, tuple) and len(color) == 3
        for color in aligned["heatmap_color"]
    )
    log_completed(f"Verified symmetric Aero-effect color range: {color_range}.")

    replacement_channel = next(
        channel
        for channel in data.get_common_channels()
        if channel != selected_channel
    )
    alignment.set_selected_channel(replacement_channel)
    assert alignment.selected_channel == replacement_channel
    assert f"delta_{replacement_channel}" in alignment.get_aligned_data()
    log_completed(
        f"Changed the selected channel to '{replacement_channel}' and "
        "reprocessed channel-dependent alignment results."
    )


def test_expected_validation_errors(loaded_datasets):
    _, baseline_df, _, aero_df = loaded_datasets

    unprocessed = TrackAlignment(baseline_df, aero_df)
    with pytest.raises(RuntimeError, match="not been processed"):
        unprocessed.get_aligned_data()
    log_completed("Confirmed aligned data cannot be read before processing.")

    with pytest.raises(ValueError, match="greater than zero"):
        TrackAlignment(
            baseline_df,
            aero_df,
            lat_column="GPS Latitude",
            lon_column="GPS Longitude",
        ).process(interpolation_step=0)
    log_completed("Confirmed a zero interpolation step is rejected.")

    with pytest.raises(ValueError, match="does not exist"):
        TrackAlignment(
            baseline_df,
            aero_df,
            lat_column="GPS Latitude",
            lon_column="GPS Longitude",
            selected_channel="channel_that_does_not_exist",
        ).process()
    log_completed("Confirmed a missing selected channel is rejected.")
