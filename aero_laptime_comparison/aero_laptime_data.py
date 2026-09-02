import pandas as pd
from core.data_manager import DataManager


class AeroLaptimeData:
    """
    Handles loading and preparing two telemetry datasets:

        Dataset A = Baseline / No Aero
        Dataset B = Aero package

    This class does not perform track alignment.
    It is responsible for loading the data and determining
    which telemetry channels can be compared.
    """

    def __init__(self):
        self.baseline_manager = DataManager()
        self.aero_manager = DataManager()

        self.baseline_df = None
        self.aero_df = None

        self.baseline_metadata = {}
        self.aero_metadata = {}

        self.common_channels = []
        self.selected_channel = None

    # ---------------------------------------------------------
    # FILE LOADING
    # ---------------------------------------------------------

    def load_baseline(self):
        """
        Opens a file dialog and loads Dataset A.
        """

        print("\nSelect BASELINE / NO AERO CSV")

        self.baseline_manager.select_file()

        self.baseline_df = (
            self.baseline_manager.import_and_validate()
        )

        self.baseline_metadata = (
            self.baseline_manager.metadata
        )

        self._update_common_channels()

        print(
            f"[INFO] Baseline loaded: "
            f"{len(self.baseline_df)} rows"
        )

        return self.baseline_df

    def load_aero(self):
        """
        Opens a file dialog and loads Dataset B.
        """

        print("\nSelect AERO CSV")

        self.aero_manager.select_file()

        self.aero_df = (
            self.aero_manager.import_and_validate()
        )

        self.aero_metadata = (
            self.aero_manager.metadata
        )

        self._update_common_channels()

        print(
            f"[INFO] Aero dataset loaded: "
            f"{len(self.aero_df)} rows"
        )

        return self.aero_df

    # ---------------------------------------------------------
    # CHANNEL HANDLING
    # ---------------------------------------------------------

    def _update_common_channels(self):
        """
        Finds channels that exist in BOTH datasets.

        Only channels present in both datasets can be directly
        compared.
        """

        if self.baseline_df is None:
            return

        if self.aero_df is None:
            return

        baseline_channels = set(
            self.baseline_df.columns
        )

        aero_channels = set(
            self.aero_df.columns
        )

        self.common_channels = sorted(
            baseline_channels.intersection(
                aero_channels
            )
        )

        print(
            f"[INFO] Common channels: "
            f"{len(self.common_channels)}"
        )

    def get_common_channels(self):
        """
        Returns channels that exist in both datasets.
        """

        return self.common_channels.copy()

    def set_selected_channel(self, channel):
        """
        Stores the channel that will later control the
        track heatmap.
        """

        if channel not in self.common_channels:
            raise ValueError(
                f"Channel '{channel}' does not exist "
                f"in both datasets."
            )

        self.selected_channel = channel

        print(
            f"[INFO] Selected channel: "
            f"{self.selected_channel}"
        )

    def get_selected_channel(self):
        """
        Returns the currently selected channel.
        """

        return self.selected_channel

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def is_ready(self):
        """
        Returns True when both datasets have been loaded.
        """

        return (
            self.baseline_df is not None
            and self.aero_df is not None
        )

    def get_summary(self):
        """
        Returns a small summary useful for debugging or
        eventually displaying in the GUI.
        """

        return {
            "baseline_rows": (
                len(self.baseline_df)
                if self.baseline_df is not None
                else 0
            ),
            "aero_rows": (
                len(self.aero_df)
                if self.aero_df is not None
                else 0
            ),
            "baseline_channels": (
                len(self.baseline_df.columns)
                if self.baseline_df is not None
                else 0
            ),
            "aero_channels": (
                len(self.aero_df.columns)
                if self.aero_df is not None
                else 0
            ),
            "common_channels": len(
                self.common_channels
            ),
            "selected_channel": self.selected_channel,
        }