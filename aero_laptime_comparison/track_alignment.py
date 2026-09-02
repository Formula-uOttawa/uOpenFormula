# track_alignment.py

import numpy as np
import pandas as pd


class TrackAlignment:
    """
    Processes two telemetry datasets and aligns them by
    distance travelled rather than timestamp.

    Dataset A:
        Baseline / No Aero

    Dataset B:
        Aero

    The class maintains two representations:

        1. Native track data
           Every row represents an original telemetry sample.

        2. Distance-aligned data
           Both datasets are interpolated onto the same
           physical distance axis.

    The selected channel can also be compared between the
    two datasets, producing:

        Aero - Baseline

    This delta is used for the Aero-effect heatmap.
    """

    EARTH_RADIUS_M = 6_371_000.0

    def __init__(
        self,
        baseline_df,
        aero_df,
        lat_column="GPS_Lat",
        lon_column="GPS_Long",
        selected_channel=None,
    ):

        self.baseline_df = baseline_df.copy()
        self.aero_df = aero_df.copy()

        self.lat_column = lat_column
        self.lon_column = lon_column

        self.selected_channel = selected_channel

        self.baseline_track = None
        self.aero_track = None

        self.aligned_data = None

        # Information about where the two recordings were aligned.
        self.aero_start_index = None
        self.aero_start_offset_m = None

        # Aero-effect heatmap range.
        #
        # These represent:
        #
        #     Aero value - Baseline value
        #
        # NOT the absolute telemetry value.
        self.color_min = None
        self.color_max = None

    # =========================================================
    # PUBLIC API
    # =========================================================

    def process(self, interpolation_step=1.0):
        """
        Complete track processing pipeline.

        Steps:

            1. Validate required columns.
            2. Create native baseline track.
            3. Create native aero track.
            4. Align the aero track start to the baseline.
            5. Create a common distance axis.
            6. Interpolate shared telemetry channels.
            7. Calculate the selected-channel delta.
            8. Generate Aero-effect heatmap colors.

        Args:
            interpolation_step:
                Distance between aligned points in metres.

        Returns:
            dict containing:

                baseline_track
                aero_track
                aligned_data
                color_range
        """

        self._validate_columns()

        self.baseline_track = self._create_native_track(
            self.baseline_df,
            dataset_name="baseline",
        )

        self.aero_track = self._create_native_track(
            self.aero_df,
            dataset_name="aero",
        )

        # Important:
        #
        # The two telemetry recordings may have started at
        # different physical positions.
        #
        # Match the aero starting position to the baseline
        # starting position before interpolation.
        self._align_track_starts()

        self.aligned_data = self._create_aligned_dataset(
            interpolation_step
        )

        if self.selected_channel is not None:
            self._generate_aero_effect_colors()

        return {
            "baseline_track": self.baseline_track,
            "aero_track": self.aero_track,
            "aligned_data": self.aligned_data,
            "color_range": self.get_color_range(),
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_columns(self):
        """
        Validates GPS columns and, if supplied, the selected
        comparison channel.
        """

        required = [
            self.lat_column,
            self.lon_column,
        ]

        for dataset_name, df in [
            ("baseline", self.baseline_df),
            ("aero", self.aero_df),
        ]:

            missing = [
                column
                for column in required
                if column not in df.columns
            ]

            if missing:
                raise ValueError(
                    f"{dataset_name} dataset is missing "
                    f"GPS columns: {missing}"
                )

        if self.selected_channel is not None:

            if self.selected_channel not in self.baseline_df.columns:
                raise ValueError(
                    f"Selected channel "
                    f"'{self.selected_channel}' "
                    f"does not exist in baseline dataset."
                )

            if self.selected_channel not in self.aero_df.columns:
                raise ValueError(
                    f"Selected channel "
                    f"'{self.selected_channel}' "
                    f"does not exist in aero dataset."
                )

    # =========================================================
    # NATIVE TRACK CREATION
    # =========================================================

    def _create_native_track(self, df, dataset_name):
        """
        Creates a native track representation.

        Every row represents an original telemetry sample.

        Added columns:

            original_index
            latitude
            longitude
            x
            y
            segment_distance
            distance

        The original telemetry channels are preserved.
        """

        track = pd.DataFrame()

        # Preserve the original DataFrame index.
        track["original_index"] = df.index

        # Convert GPS values to numeric.
        track["latitude"] = pd.to_numeric(
            df[self.lat_column],
            errors="coerce",
        )

        track["longitude"] = pd.to_numeric(
            df[self.lon_column],
            errors="coerce",
        )

        # Keep only rows with valid GPS coordinates.
        track = track.dropna(
            subset=[
                "latitude",
                "longitude",
            ]
        ).reset_index(drop=True)

        if len(track) < 2:
            raise ValueError(
                f"{dataset_name} does not contain enough "
                f"valid GPS points to construct a track."
            )

        # -----------------------------------------------------
        # Convert GPS to local Cartesian coordinates.
        #
        # Equirectangular approximation.
        # Appropriate for the relatively small area of a
        # race track.
        # -----------------------------------------------------

        lat0 = np.radians(
            track["latitude"].iloc[0]
        )

        lon0 = np.radians(
            track["longitude"].iloc[0]
        )

        lat = np.radians(
            track["latitude"].to_numpy()
        )

        lon = np.radians(
            track["longitude"].to_numpy()
        )

        x = (
            self.EARTH_RADIUS_M
            * (lon - lon0)
            * np.cos(lat0)
        )

        y = (
            self.EARTH_RADIUS_M
            * (lat - lat0)
        )

        track["x"] = x
        track["y"] = y

        # -----------------------------------------------------
        # Distance between consecutive GPS points.
        # -----------------------------------------------------

        dx = np.diff(
            x,
            prepend=x[0],
        )

        dy = np.diff(
            y,
            prepend=y[0],
        )

        segment_distance = np.sqrt(
            dx ** 2 + dy ** 2
        )

        segment_distance[0] = 0.0

        track["segment_distance"] = (
            segment_distance
        )

        # -----------------------------------------------------
        # Cumulative distance.
        # -----------------------------------------------------

        track["distance"] = np.cumsum(
            segment_distance
        )

        # -----------------------------------------------------
        # Attach every original telemetry channel.
        # -----------------------------------------------------

        for column in df.columns:

            if column in [
                self.lat_column,
                self.lon_column,
            ]:
                continue

            values = pd.to_numeric(
                df.loc[
                    track["original_index"],
                    column,
                ],
                errors="coerce",
            )

            track[column] = values.to_numpy()

        return track

    # =========================================================
    # TRACK START ALIGNMENT
    # =========================================================

    def _align_track_starts(self):
        """
        Aligns the beginning of the aero recording with the
        beginning of the baseline recording.

        The first baseline GPS point becomes the reference.

        The closest point on the aero track becomes the
        aero distance-zero point.

        This handles situations where the two telemetry
        recordings started at slightly different positions
        around the circuit.
        """

        baseline_x0 = (
            self.baseline_track["x"].iloc[0]
        )

        baseline_y0 = (
            self.baseline_track["y"].iloc[0]
        )

        distances_to_baseline_start = np.sqrt(
            (
                self.aero_track["x"]
                - baseline_x0
            ) ** 2
            +
            (
                self.aero_track["y"]
                - baseline_y0
            ) ** 2
        )

        closest_index = (
            distances_to_baseline_start.idxmin()
        )

        closest_distance = (
            distances_to_baseline_start.loc[
                closest_index
            ]
        )

        self.aero_start_index = closest_index

        self.aero_start_offset_m = (
            float(closest_distance)
        )

        # Distance of the matching aero point.
        aero_start_distance = (
            self.aero_track.loc[
                closest_index,
                "distance",
            ]
        )

        # Baseline starts at zero.
        self.baseline_track[
            "aligned_distance"
        ] = self.baseline_track[
            "distance"
        ]

        # Shift aero so its matching point becomes zero.
        self.aero_track[
            "aligned_distance"
        ] = (
            self.aero_track["distance"]
            - aero_start_distance
        )

        # Remove any negative values before the matching
        # start point. Those points belong to the portion of
        # the recording before the alignment position.
        self.aero_track = (
            self.aero_track[
                self.aero_track["aligned_distance"] >= 0
            ]
            .reset_index(drop=True)
        )

    # =========================================================
    # DISTANCE-ALIGNED DATASET
    # =========================================================

    def _create_aligned_dataset(
        self,
        interpolation_step,
    ):
        """
        Creates a common distance axis and interpolates both
        telemetry datasets onto it.

        Only channels existing in BOTH datasets are included.

        Structural GPS/track columns are excluded.

        The result contains:

            distance
            baseline_<channel>
            aero_<channel>

        If a selected channel exists, it also contains:

            delta_<selected_channel>

        where:

            delta = aero - baseline
        """

        if interpolation_step <= 0:
            raise ValueError(
                "Interpolation step must be greater than zero."
            )

        baseline = self.baseline_track
        aero = self.aero_track

        max_distance = min(
            baseline["aligned_distance"].max(),
            aero["aligned_distance"].max(),
        )

        if max_distance <= 0:
            raise ValueError(
                "Unable to determine a common track distance."
            )

        common_distance = np.arange(
            0,
            max_distance,
            interpolation_step,
        )

        # Include the final common point.
        if (
            len(common_distance) == 0
            or common_distance[-1] < max_distance
        ):
            common_distance = np.append(
                common_distance,
                max_distance,
            )

        aligned = pd.DataFrame()

        aligned["distance"] = common_distance

        # -----------------------------------------------------
        # X/Y coordinates
        # -----------------------------------------------------

        aligned["baseline_x"] = np.interp(
            common_distance,
            baseline["aligned_distance"],
            baseline["x"],
        )

        aligned["baseline_y"] = np.interp(
            common_distance,
            baseline["aligned_distance"],
            baseline["y"],
        )

        aligned["aero_x"] = np.interp(
            common_distance,
            aero["aligned_distance"],
            aero["x"],
        )

        aligned["aero_y"] = np.interp(
            common_distance,
            aero["aligned_distance"],
            aero["y"],
        )

        # -----------------------------------------------------
        # Shared telemetry channels
        # -----------------------------------------------------

        shared_columns = (
            set(baseline.columns)
            .intersection(aero.columns)
        )

        excluded_columns = {
            "original_index",
            "latitude",
            "longitude",
            "x",
            "y",
            "segment_distance",
            "distance",
            "aligned_distance",
        }

        shared_channels = sorted(
            shared_columns - excluded_columns
        )

        for channel in shared_channels:

            baseline_values = pd.to_numeric(
                baseline[channel],
                errors="coerce",
            )

            aero_values = pd.to_numeric(
                aero[channel],
                errors="coerce",
            )

            # np.interp does not handle NaN values correctly,
            # so only interpolate channels containing usable
            # numeric data.
            baseline_valid = (
                baseline_values.notna()
            )

            aero_valid = (
                aero_values.notna()
            )

            if baseline_valid.sum() < 2:
                continue

            if aero_valid.sum() < 2:
                continue

            baseline_distance = (
                baseline["aligned_distance"]
                .to_numpy()[baseline_valid.to_numpy()]
            )

            baseline_numeric_values = (
                baseline_values.to_numpy()[
                    baseline_valid.to_numpy()
                ]
            )

            aero_distance = (
                aero["aligned_distance"]
                .to_numpy()[aero_valid.to_numpy()]
            )

            aero_numeric_values = (
                aero_values.to_numpy()[
                    aero_valid.to_numpy()
                ]
            )

            aligned[
                f"baseline_{channel}"
            ] = np.interp(
                common_distance,
                baseline_distance,
                baseline_numeric_values,
            )

            aligned[
                f"aero_{channel}"
            ] = np.interp(
                common_distance,
                aero_distance,
                aero_numeric_values,
            )

        # -----------------------------------------------------
        # Selected-channel Aero effect
        # -----------------------------------------------------

        if self.selected_channel is not None:

            baseline_column = (
                f"baseline_{self.selected_channel}"
            )

            aero_column = (
                f"aero_{self.selected_channel}"
            )

            if (
                baseline_column in aligned.columns
                and aero_column in aligned.columns
            ):

                aligned[
                    f"delta_{self.selected_channel}"
                ] = (
                    aligned[aero_column]
                    - aligned[baseline_column]
                )

        return aligned

    # =========================================================
    # POINT COMPARISON
    # =========================================================

    def get_comparison(self, distance):
        """
        Returns the telemetry state of both datasets at the
        requested aligned distance.

        Example:

            comparison = alignment.get_comparison(850)

        Returns:

            requested_distance
            actual_distance
            baseline
            aero
            selected_channel
        """

        if self.aligned_data is None:
            raise RuntimeError(
                "Track alignment has not been processed yet."
            )

        distances = (
            self.aligned_data[
                "distance"
            ].to_numpy()
        )

        index = np.abs(
            distances - distance
        ).argmin()

        row = self.aligned_data.iloc[index]

        comparison = {
            "requested_distance": float(distance),
            "actual_distance": float(
                row["distance"]
            ),
            "baseline": {},
            "aero": {},
        }

        for column in self.aligned_data.columns:

            if column == "distance":
                continue

            if column.startswith("baseline_"):

                channel = column.replace(
                    "baseline_",
                    "",
                    1,
                )

                comparison["baseline"][
                    channel
                ] = row[column]

            elif column.startswith("aero_"):

                channel = column.replace(
                    "aero_",
                    "",
                    1,
                )

                comparison["aero"][
                    channel
                ] = row[column]

        # -----------------------------------------------------
        # Selected channel comparison
        # -----------------------------------------------------

        if self.selected_channel is not None:

            baseline_value = (
                comparison["baseline"].get(
                    self.selected_channel
                )
            )

            aero_value = (
                comparison["aero"].get(
                    self.selected_channel
                )
            )

            if (
                baseline_value is not None
                and aero_value is not None
            ):

                comparison[
                    "selected_channel"
                ] = {
                    "channel": self.selected_channel,
                    "baseline": baseline_value,
                    "aero": aero_value,
                    "delta": (
                        aero_value
                        - baseline_value
                    ),
                }

        return comparison

    # =========================================================
    # AERO-EFFECT HEATMAP
    # =========================================================

    def _generate_aero_effect_colors(self):
        """
        Generates colors based on the DIFFERENCE between
        Aero and Baseline.

        The heatmap represents:

            Aero - Baseline

        Therefore:

            Negative = Aero lower than Baseline
            Zero     = Aero equal to Baseline
            Positive = Aero higher than Baseline

        Both tracks use the SAME delta color scale.

        This is intentionally different from an absolute
        telemetry heatmap.

        The heatmap answers:

            "Where does the Aero configuration change
             the selected telemetry channel?"
        """

        if self.selected_channel is None:
            return

        baseline_values = pd.to_numeric(
            self.baseline_track[
                self.selected_channel
            ],
            errors="coerce",
        )

        aero_values = pd.to_numeric(
            self.aero_track[
                self.selected_channel
            ],
            errors="coerce",
        )

        # The native tracks have different sampling positions,
        # so the Aero-effect heatmap is based on the common
        # distance-aligned data.
        delta_column = (
            f"delta_{self.selected_channel}"
        )

        if (
            self.aligned_data is None
            or delta_column not in self.aligned_data.columns
        ):
            raise ValueError(
                f"Unable to generate Aero-effect heatmap "
                f"for channel '{self.selected_channel}'."
            )

        delta_values = pd.to_numeric(
            self.aligned_data[
                delta_column
            ],
            errors="coerce",
        )

        valid_delta_values = delta_values.dropna()

        if valid_delta_values.empty:
            raise ValueError(
                "Selected channel contains no usable "
                "numeric delta values."
            )

        maximum_effect = max(
            abs(float(valid_delta_values.min())),
            abs(float(valid_delta_values.max())),
        )

        if maximum_effect == 0:
            maximum_effect = 1.0

        self.color_min = -maximum_effect
        self.color_max = maximum_effect

        self.aligned_data[
            "heatmap_color"
        ] = delta_values.apply(
            self._delta_to_color
        )


        if delta_values.empty:
            raise ValueError(
                "Selected channel contains no usable "
                "numeric delta values."
            )

        # -----------------------------------------------------
        # Symmetric color range.
        #
        # Example:
        #
        # Actual delta range:
        #
        #     -3 to +8
        #
        # Heatmap range:
        #
        #     -8 to +8
        #
        # This makes zero the visual midpoint.
        # -----------------------------------------------------

        maximum_effect = max(
            abs(float(delta_values.min())),
            abs(float(delta_values.max())),
        )

        if maximum_effect == 0:
            maximum_effect = 1.0

        self.color_min = -maximum_effect
        self.color_max = maximum_effect

        # -----------------------------------------------------
        # Generate colors for the aligned points.
        #
        # These colors represent the Aero effect at each
        # physical location on the track.
        # -----------------------------------------------------

        self.aligned_data[
            "heatmap_color"
        ] = delta_values.reindex(
            self.aligned_data.index
        ).apply(
            self._delta_to_color
        )

        # -----------------------------------------------------
        # Also assign each native track point a color by
        # interpolating the aligned delta scale onto the
        # native track's aligned distance.
        #
        # This allows the GUI to draw the actual GPS track
        # using Aero-effect colors.
        # -----------------------------------------------------

        common_distance = (
            self.aligned_data[
                "distance"
            ].to_numpy()
        )

        common_delta = (
            self.aligned_data[
                delta_column
            ].to_numpy()
        )

        # Baseline native points.
        baseline_delta = np.interp(
            self.baseline_track[
                "aligned_distance"
            ],
            common_distance,
            common_delta,
        )

        # Aero native points.
        aero_delta = np.interp(
            self.aero_track[
                "aligned_distance"
            ],
            common_distance,
            common_delta,
        )

        self.baseline_track[
            "aero_effect"
        ] = baseline_delta

        self.aero_track[
            "aero_effect"
        ] = aero_delta

        self.baseline_track[
            "heatmap_color"
        ] = [
            self._delta_to_color(value)
            for value in baseline_delta
        ]

        self.aero_track[
            "heatmap_color"
        ] = [
            self._delta_to_color(value)
            for value in aero_delta
        ]

    # =========================================================
    # DELTA → COLOR
    # =========================================================

    def _delta_to_color(self, value):
        """
        Converts an Aero-effect delta into an RGB color.

        Color meaning:

            Blue   = Aero significantly lower
            Cyan
            Green  = small/zero effect
            Yellow
            Red    = Aero significantly higher

        The scale is symmetric around zero.

        Returned as:

            (R, G, B)
        """

        if pd.isna(value):
            return (128, 128, 128)

        if (
            self.color_min is None
            or self.color_max is None
        ):
            return (128, 128, 128)

        if self.color_max == self.color_min:
            normalized = 0.5

        else:

            normalized = (
                value - self.color_min
            ) / (
                self.color_max
                - self.color_min
            )

            normalized = max(
                0.0,
                min(1.0, normalized),
            )

        # -----------------------------------------------------
        # Blue -> Cyan -> Green -> Yellow -> Red
        #
        # Green is the zero-effect midpoint.
        # -----------------------------------------------------

        stops = [
            (0.00, (0, 0, 255)),
            (0.25, (0, 255, 255)),
            (0.50, (0, 255, 0)),
            (0.75, (255, 255, 0)),
            (1.00, (255, 0, 0)),
        ]

        for i in range(
            len(stops) - 1
        ):

            lower_position, lower_color = (
                stops[i]
            )

            upper_position, upper_color = (
                stops[i + 1]
            )

            if (
                lower_position
                <= normalized
                <= upper_position
            ):

                local_position = (
                    normalized
                    - lower_position
                ) / (
                    upper_position
                    - lower_position
                )

                r = int(
                    lower_color[0]
                    + (
                        upper_color[0]
                        - lower_color[0]
                    )
                    * local_position
                )

                g = int(
                    lower_color[1]
                    + (
                        upper_color[1]
                        - lower_color[1]
                    )
                    * local_position
                )

                b = int(
                    lower_color[2]
                    + (
                        upper_color[2]
                        - lower_color[2]
                    )
                    * local_position
                )

                return (r, g, b)

        return (255, 0, 0)

    # =========================================================
    # CONVENIENCE METHODS
    # =========================================================

    def get_track_points(self):
        """
        Returns the native telemetry points.

        These are NOT interpolated.

        Useful for:

            - GPS track plotting
            - heatmap rendering
            - debugging
            - inspecting native telemetry samples
        """

        return {
            "baseline": self.baseline_track,
            "aero": self.aero_track,
        }

    def get_aligned_data(self):
        """
        Returns the common distance-aligned DataFrame.
        """

        if self.aligned_data is None:
            raise RuntimeError(
                "Track alignment has not been processed yet."
            )

        return self.aligned_data

    def get_color_range(self):
        """
        Returns the Aero-effect heatmap color range.

        The values represent:

            Aero - Baseline

        Example:

            {
                "min": -10.0,
                "max": 10.0,
                "channel": "Speed"
            }
        """

        return {
            "min": self.color_min,
            "max": self.color_max,
            "channel": self.selected_channel,
        }

    def set_selected_channel(self, channel):
        """
        Changes the selected comparison channel.

        The data must be reprocessed after changing the channel
        in order to regenerate the delta and heatmap colors.
        """

        if channel not in self.baseline_df.columns:
            raise ValueError(
                f"Channel '{channel}' does not exist "
                f"in baseline dataset."
            )

        if channel not in self.aero_df.columns:
            raise ValueError(
                f"Channel '{channel}' does not exist "
                f"in aero dataset."
            )

        self.selected_channel = channel

        # Clear channel-dependent results.
        self.color_min = None
        self.color_max = None

        if self.aligned_data is not None:

            delta_column = (
                f"delta_{channel}"
            )

            # Re-run the complete processing pipeline
            # so the aligned data and heatmap are consistent.
            self.process()

    def get_aero_start_alignment(self):
        """
        Returns information about how the two track starts
        were matched.
        """

        return {
            "aero_start_index": self.aero_start_index,
            "aero_start_offset_m": (
                self.aero_start_offset_m
            ),
        }