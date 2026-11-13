from pathlib import Path
from typing import Optional

from .aim_dll_importer_exceptions import (
    AimImporterInternalSystemError,
    AimImporterFileNotFoundError,
    AimImporterFailedToParseFileError,
    AimImporterFailedToCloseFileError,
    AimImporterFailedToReadFileError,
    AimImporterNoSessionPresentError,
    AimImporterInvalidGPSFrequencyError,
)
from .aim_file import AimFile
from .aim_types import (
    AimChannelMetadata,
    AimChannelSamples,
    AimChannel,
    AimLap,
    AimGPSChannel
)

from .lib_wrapper.aim_dll_wrapper import AimLibraryWrapper
from .lib_wrapper.aim_dll_wrapper_exceptions import AimDLLWrapperException


class AimFileContextManager:
    """
    High-level context manager for interacting with AIM data files.

    This class wraps the low-level `AimLibraryWrapper` DLL interface and provides
    safe, exception-based access to AIM file metadata, channels, laps, and session
    information.
    """

    _base_path: Path
    _lib_wrapper: AimLibraryWrapper

    _license_path: Optional[str]
    _sample_freq: float

    def __init__(
            self,
            base_path: Path | str,
            sample_freq: Optional[float] = 100,
            license_path: Optional[str] = None
    ):
        """
        Initialize the context manager.

        Parameters
        ----------
        base_path : Path or str
            Base directory where AIM files are located.
        """
        self._base_path = Path(base_path)
        self._license_path = license_path

        self._init_lib_wrapper()
        self._init_gps_channels(sample_freq)


    def _init_lib_wrapper(self):
        """Initialize the AIM DLL library wrapper.

        The DLL is loaded from the ``lib`` directory located relative to this
        module.

        Raises
        ------
        AimImporterInternalSystemError
            If the library wrapper cannot be initialized.
        """
        dir_path = Path(__file__).resolve().parent
        dll_path = dir_path / "lib" / "MatLabXRK-2022-64-ReleaseU.dll"
        self._lib_wrapper = AimLibraryWrapper(str(dll_path))

    def _init_gps_channels(self, sample_freq: float):
        """Configure the GPS channel sample frequency.

        Parameters
        ----------
        sample_freq : float
            GPS sample frequency to configure in the AIM DLL.

        Raises
        ------
        AimImporterInternalSystemError
            If the AIM DLL reports a failure while setting the sample frequency
            or raises an internal exception.
        AimImporterInvalidGPSFrequencyError
            If the specified GPS sample frequency is invalid.
        """
        self._sample_freq = sample_freq

        try:
            result = self._lib_wrapper.set_gps_sample_frequency(self._sample_freq)

            if result == 1:
                raise AimImporterInternalSystemError("Failed to set sample frequency")
            if result == 2:
                raise AimImporterInvalidGPSFrequencyError()

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def open_aim_file(self, file_name: Path | str) -> Optional[AimFile]:
        """
        Open an AIM file and return an `AimFile` instance.

        Parameters
        ----------
        file_name : Path or str
            File name relative to the base path.

        Returns
        -------
        AimFile or None
            The opened AIM file wrapper, or None if not found.

        Raises
        ------
        AimImporterFileNotFoundError
            If the DLL returns a file descriptor of 0.
        AimImporterFailedToParseFileError
            If the DLL returns a negative file descriptor.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        full_path = self._base_path / Path(file_name)

        try:
            fd = self._lib_wrapper.open_file(str(full_path), self._license_path)

            if fd == 0:
                raise AimImporterFileNotFoundError()

            if fd < 0:
                raise AimImporterFailedToParseFileError()

            return AimFile(fd, self)

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def close_aim_file(self, file: AimFile):
        """
        Close an AIM file.

        Parameters
        ----------
        file : AimFile
            The file instance to close.

        Raises
        ------
        AimImporterFailedToCloseFileError
            If the DLL returns <= 0.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            fd = self._lib_wrapper.close_file(file.id)
            if fd <= 0:
                raise AimImporterFailedToCloseFileError()

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_logger_id(self, file: AimFile) -> Optional[int]:
        """
        Retrieve the logger ID associated with the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        int or None
            Logger ID, or None if unavailable.

        Raises
        ------
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            return self._lib_wrapper.get_logger_id(file.id)
        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_devices(self, file: AimFile) -> list[int]:
        """
        Retrieve all device IDs present in the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        list of int
            List of device IDs.

        Raises
        ------
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            devices = []
            device_count = self._lib_wrapper.get_number_of_devices(file.id)

            for device_idx in range(device_count):
                device_id = self._lib_wrapper.get_device_id(file.id, device_idx)
                devices.append(device_id)

            return devices

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_vehicle_name(self, file: AimFile) -> str:
        """
        Retrieve the vehicle name stored in the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        str
            Vehicle name.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the name is missing.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            vehicle_name = self._lib_wrapper.get_vehicle_name(file.id)
            if vehicle_name is None:
                raise AimImporterFailedToReadFileError()
            return vehicle_name

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_track_name(self, file: AimFile) -> str:
        """
        Retrieve the track name stored in the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        str
            Track name.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the name is missing.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            track_name = self._lib_wrapper.get_track_name(file.id)
            if track_name is None:
                raise AimImporterFailedToReadFileError()
            return track_name

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_racer_name(self, file: AimFile) -> str:
        """
        Retrieve the racer name stored in the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        str
            Racer name.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the name is missing.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            racer_name = self._lib_wrapper.get_racer_name(file.id)
            if racer_name is None:
                raise AimImporterFailedToReadFileError()
            return racer_name

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_championship_name(self, file: AimFile) -> str:
        """
        Retrieve the championship name stored in the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        str
            Championship name.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the name is missing.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            championship_name = self._lib_wrapper.get_championship_name(file.id)
            if championship_name is None:
                raise AimImporterFailedToReadFileError()
            return championship_name

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_session_type_name(self, file: AimFile) -> str:
        """
        Retrieve the session type name stored in the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        str
            Session type name.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the name is missing.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            session_type_name = self._lib_wrapper.get_session_type_name(file.id)
            if session_type_name is None:
                raise AimImporterFailedToReadFileError()
            return session_type_name

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_laps(self, file: AimFile) -> list[AimLap]:
        """
        Retrieve lap information from the AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        list of AimLap
            Laps with start time and duration.

        Raises
        ------
        AimImporterFailedToReadFileError
            If lap count or lap info is invalid.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            lap_count = self._lib_wrapper.get_laps_count(file.id)
            if lap_count < 0:
                raise AimImporterFailedToReadFileError()

            laps = []
            for lap_idx in range(lap_count):
                start, duration = self._lib_wrapper.get_lap_info(file.id, lap_idx)
                if start is None or duration is None:
                    raise AimImporterFailedToReadFileError()
                laps.append(AimLap(lap_idx, start, duration))

            return laps

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_session_duration(self, file: AimFile) -> float:
        """
        Retrieve the total session duration.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.

        Returns
        -------
        float
            Session duration in seconds.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the DLL returns a negative result.
        AimImporterNoSessionPresentError
            If the DLL returns zero (no session).
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            res, duration = self._lib_wrapper.get_session_duration(file.id)
            if res < 0:
                raise AimImporterFailedToReadFileError()
            if res == 0:
                raise AimImporterNoSessionPresentError()
            return duration

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_channels(self, file: AimFile, lap: Optional[AimLap] = None) -> list[AimChannel]:
        """
        Retrieve all channels and their metadata and samples.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.
        lap : AimLap, optional
            Lap to get channel data for

        Returns
        -------
        list of AimChannel
            Channels with metadata and sample data.

        Raises
        ------
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        channels = []

        try:
            channel_count = self._lib_wrapper.get_channels_count(file.id)
        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

        for channel_idx in range(channel_count):
            metadata = self._get_channel_metadata(file, channel_idx)
            samples = self._get_channel_samples(file, channel_idx, lap)
            channels.append(AimChannel(metadata=metadata, samples=samples))

        return channels

    def _get_channel_metadata(self, file: AimFile, channel_id: int) -> AimChannelMetadata:
        """
        Retrieve metadata for a specific channel.

        Parameters
        ----------
        file : AimFile
            The AIM file instance.
        channel_id : int
            Channel index.

        Returns
        -------
        AimChannelMetadata
            Channel metadata including name and units.

        Raises
        ------
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            name = self._lib_wrapper.get_channel_name(file.id, channel_id)
            name_no_space = self._lib_wrapper.get_channel_name_no_spaces(file.id, channel_id)
            unit = self._lib_wrapper.get_channel_units(file.id, channel_id)

            return AimChannelMetadata(
                id=channel_id,
                name=name,
                name_no_spaces=name_no_space,
                unit=unit,
            )

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def _get_channel_samples(
            self,
            file: AimFile,
            channel_id: int,
            lap: Optional[AimLap],
    ) -> AimChannelSamples:
        """Retrieve sample timestamps and values for a specific channel.

        Parameters
        ----------
        file : AimFile
            The AIM file instance containing the channel data.
        channel_id : int
            Zero-based index of the channel.
        lap : AimLap, optional
            If provided, retrieve samples for this lap only. If ``None``,
            retrieve samples for the entire session.

        Returns
        -------
        AimChannelSamples
            Sample timestamps and values for the requested channel.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the DLL reports an error reading channel samples
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            if lap is None:
                count, timestamps, values = self._lib_wrapper.get_channel_samples(
                    file.id,
                    channel_id,
                )
            else:
                count, timestamps, values = self._lib_wrapper.get_lap_channel_samples(
                    file.id,
                    channel_id,
                    lap.id,
                )

            if count < 0:
                raise AimImporterFailedToReadFileError()

            return AimChannelSamples(timestamps=timestamps, values=values)

        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def get_gps_channels(
            self,
            file: AimFile,
            lap: Optional[AimLap] = None,
    ) -> list[AimGPSChannel]:
        """Retrieve all GPS channels from an AIM file.

        Parameters
        ----------
        file : AimFile
            The AIM file containing the GPS channel data.
        lap : AimLap, optional
            If provided, retrieve samples for this lap only. If ``None``,
            retrieve samples for the entire session.

        Returns
        -------
        list[AimGPSChannel]
            A list of GPS channels, including their metadata and samples.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the DLL reports an error in reading channels
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception while retrieving
            the channel count, metadata, or samples.
        """
        try:
            channel_count = self._lib_wrapper.get_gps_channels_count(file.id)
        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

        channels: list[AimGPSChannel] = []
        for channel_idx in range(channel_count):
            metadata = self._get_gps_channel_metadata(file, channel_idx)
            samples = self._get_gps_channel_samples(file, channel_idx, lap)
            channels.append(
                AimGPSChannel(
                    metadata=metadata,
                    samples=samples,
                )
            )

        return channels

    def _get_gps_channel_metadata(
            self,
            file: AimFile,
            channel_id: int,
    ) -> AimChannelMetadata:
        """Retrieve metadata for a specific GPS channel.

        Parameters
        ----------
        file : AimFile
            The AIM file containing the GPS channel.
        channel_id : int
            Zero-based index of the GPS channel.

        Returns
        -------
        AimChannelMetadata
            Metadata describing the GPS channel, including its ID, name,
            normalized name, and units.

        Raises
        ------
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            name = self._lib_wrapper.get_gps_channel_name(file.id, channel_id)
            name_no_spaces = self._lib_wrapper.get_gps_channel_name_no_spaces(
                file.id,
                channel_id,
            )
            units = self._lib_wrapper.get_gps_channel_units(file.id, channel_id)

            return AimChannelMetadata(
                id=channel_id,
                name=name,
                name_no_spaces=name_no_spaces,
                unit=units,
            )
        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

    def _get_gps_channel_samples(
            self,
            file: AimFile,
            channel_id: int,
            lap: Optional[AimLap],
    ) -> AimChannelSamples:
        """Retrieve sample timestamps and values for a specific GPS channel.

        Parameters
        ----------
        file : AimFile
            The AIM file containing the GPS channel data.
        channel_id : int
            Zero-based index of the GPS channel.
        lap : AimLap, optional
            If provided, retrieve samples for this lap only. If ``None``,
            retrieve samples for the entire session.

        Returns
        -------
        AimChannelSamples
            Sample timestamps and values for the requested GPS channel.

        Raises
        ------
        AimImporterFailedToReadFileError
            If the DLL reports an error in reading the samples.
        AimImporterInternalSystemError
            If the DLL wrapper raises an internal exception.
        """
        try:
            if lap is None:
                count, timestamps, values = self._lib_wrapper.get_gps_channel_samples(
                    file.id,
                    channel_id,
                )
            else:
                count, timestamps, values = (
                    self._lib_wrapper.get_lap_gps_channel_samples(
                        file.id,
                        channel_id,
                        lap.id,
                    )
                )
        except AimDLLWrapperException as e:
            raise AimImporterInternalSystemError(str(e))

        if count < 0:
            raise AimImporterFailedToReadFileError()

        return AimChannelSamples(
            timestamps=timestamps,
            values=values,
        )