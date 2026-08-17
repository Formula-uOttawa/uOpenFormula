import ctypes
from typing import Optional

from .aim_dll_function_registry import (
    AimDLLFunctionRegistry,
)


class AimLibraryWrapper:
    """Python wrapper around the AiM DLL API.

    This class provides a Python-friendly interface to the exported AiM DLL
    functions. DLL function lookup and ctypes configuration are delegated to
    ``AimDLLFunctionRegistry``.

    Args:
        dll_path: Path to the AiM DLL shared library.

    Raises:
        OSError: If the DLL cannot be loaded.
    """

    _function_registry: AimDLLFunctionRegistry

    def __init__(self, dll_path: str):
        """Initialize the AiM DLL wrapper.

        Args:
            dll_path: Path to the AiM DLL shared library.
        """
        self._init_dll(dll_path)

    def _init_dll(self, dll_path: str) -> None:
        """Load the DLL and initialize the function registry.

        Args:
            dll_path: Path to the AiM DLL shared library.

        Raises:
            OSError: If the DLL cannot be loaded.
        """
        dll: ctypes.CDLL = ctypes.CDLL(dll_path)
        self._function_registry = AimDLLFunctionRegistry(dll)

    def open_file(
        self,
        file_name: str,
        license_file_name: Optional[str] = None,
    ) -> int:
        """Open an XRK file.

        If a license file is supplied, the licensed version of the native
        function is used.

        Args:
            file_name: Full path to the XRK file.
            license_file_name: Optional full path to the license file.

        Returns:
            Internal file index on success. ``0`` indicates that the file
            could be opened but could not be parsed. A negative value
            indicates an error.
        """
        if license_file_name is None:
            return self._open_file_no_license(file_name)

        return self._open_file_with_license(
            file_name,
            license_file_name,
        )

    def _open_file_no_license(self, file_name: str) -> int:
        """Open an XRK file without a license file.

        Args:
            file_name: Full path to the XRK file.

        Returns:
            Internal file index or an error code.
        """
        open_file_callable = self._function_registry.get_function(
            "open_file"
        )
        return open_file_callable(file_name)

    def _open_file_with_license(
        self,
        file_name: str,
        license_file_name: str,
    ) -> int:
        """Open an XRK file using a license file.

        Args:
            file_name: Full path to the XRK file.
            license_file_name: Full path to the license file.

        Returns:
            Internal file index or an error code.
        """
        open_file_callable = self._function_registry.get_function(
            "open_file_with_licence"
        )
        return open_file_callable(file_name, license_file_name)

    def get_last_open_error(self) -> Optional[str]:
        """Get information about the last file-open error.

        Returns:
            Error message, or ``None`` if the native function returns NULL.
        """
        callable_ = self._function_registry.get_function(
            "get_last_open_error"
        )
        return callable_()

    def close_file(self, file_name_or_index: int | str) -> int:
        """Close an open XRK file.

        Args:
            file_name_or_index: Internal file index returned by ``open_file``,
                or the full path of the file.

        Returns:
            Internal file index of the closed file, or a negative value
            on error.

        Raises:
            TypeError: If ``file_name_or_index`` is not an ``int`` or ``str``.
        """
        match file_name_or_index:
            case int(index):
                return self._close_file_by_idx(index)
            case str(file_name):
                return self._close_file_by_name(file_name)
            case _:
                raise TypeError("Expected int or string")

    def _close_file_by_idx(self, idx: int) -> int:
        """Close an XRK file using its internal index.

        Args:
            idx: Internal file index.

        Returns:
            Internal file index of the closed file, or a negative value
            on error.
        """
        callable_ = self._function_registry.get_function("close_file_i")
        return callable_(idx)

    def _close_file_by_name(self, file_name: str) -> int:
        """Close an XRK file using its full path.

        Args:
            file_name: Full path to the XRK file.

        Returns:
            Internal file index of the closed file, or a negative value
            on error.
        """
        callable_ = self._function_registry.get_function("close_file_n")
        return callable_(file_name)

    def get_logger_id(self, file_idx: int) -> int:
        """Get the logger serial number.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Logger serial number.
        """
        callable_ = self._function_registry.get_function("get_logger_id")
        return callable_(file_idx)

    def get_number_of_devices(self, file_idx: int) -> int:
        """Get the number of devices in the AiM network.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Number of devices.
        """
        callable_ = self._function_registry.get_function(
            "get_number_of_devices"
        )
        return callable_(file_idx)

    def get_device_id(self, file_idx: int, device_idx: int) -> int:
        """Get the serial number of a device.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            device_idx: Zero-based device index.

        Returns:
            Device serial number.
        """
        callable_ = self._function_registry.get_function("get_device_id")
        return callable_(file_idx, device_idx)

    def get_vehicle_name(self, file_idx: int) -> Optional[str]:
        """Get the vehicle name.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Vehicle name, or ``None`` if the native function returns NULL.
        """
        callable_ = self._function_registry.get_function("get_vehicle_name")
        return callable_(file_idx)

    def get_track_name(self, file_idx: int) -> Optional[str]:
        """Get the track name.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Track name, or ``None`` if the native function returns NULL.
        """
        callable_ = self._function_registry.get_function("get_track_name")
        return callable_(file_idx)

    def get_racer_name(self, file_idx: int) -> Optional[str]:
        """Get the racer name.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Racer name, or ``None`` if the native function returns NULL.
        """
        callable_ = self._function_registry.get_function("get_racer_name")
        return callable_(file_idx)

    def get_championship_name(self, file_idx: int) -> Optional[str]:
        """Get the championship name.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Championship name, or ``None`` if the native function returns
            NULL.
        """
        callable_ = self._function_registry.get_function(
            "get_championship_name"
        )
        return callable_(file_idx)

    def get_session_type_name(self, file_idx: int) -> Optional[str]:
        """Get the session type name.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Session type name, or ``None`` if the native function returns
            NULL.
        """
        callable_ = self._function_registry.get_function(
            "get_session_type_name"
        )
        return callable_(file_idx)

    def get_date_and_time(self, file_idx: int):
        """Get the session date and time.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Pointer/value returned by the native ``struct tm`` function.
        """
        callable_ = self._function_registry.get_function(
            "get_date_and_time"
        )
        return callable_(file_idx)

    def get_laps_count(self, file_idx: int) -> int:
        """Get the number of laps in the XRK file.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Number of laps, ``0`` if there are no laps, or a negative
            value on error.
        """
        callable_ = self._function_registry.get_function("get_laps_count")
        return callable_(file_idx)

    def get_lap_info(
        self,
        file_idx: int,
        lap_idx: int,
    ):
        """Get the start time and duration of a lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.

        Returns:
            The result returned by the native function together with the
            populated start-time and duration buffers.
        """
        start_time = ctypes.c_double()
        duration = ctypes.c_double()

        callable_ = self._function_registry.get_function("get_lap_info")

        result = callable_(
            file_idx,
            lap_idx,
            ctypes.byref(start_time),
            ctypes.byref(duration),
        )

        return result, start_time.value, duration.value

    def get_session_duration(self, file_idx: int) -> tuple[int, float]:
        """Get the total session duration.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            A tuple containing the native result code and session duration.
        """
        duration = ctypes.c_double()

        callable_ = self._function_registry.get_function(
            "get_session_duration"
        )

        result = callable_(
            file_idx,
            ctypes.byref(duration),
        )

        return result, duration.value

    # ------------------------------------------------------------------
    # Standard channel functions
    # ------------------------------------------------------------------

    def get_channels_count(self, file_idx: int) -> int:
        """Get the number of standard channels.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Number of channels or a negative value on error.
        """
        callable_ = self._function_registry.get_function(
            "get_channels_count"
        )
        return callable_(file_idx)

    def get_channel_name(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get a channel name.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Channel index.

        Returns:
            Channel name, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_channel_name"
        )
        return callable_(file_idx, channel_idx)

    def get_channel_name_no_spaces(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get a channel name without spaces.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Channel index.

        Returns:
            Channel name without spaces, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_channel_name_no_spaces"
        )
        return callable_(file_idx, channel_idx)

    def get_channel_units(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get the units associated with a channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Channel index.

        Returns:
            Channel units, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_channel_units"
        )
        return callable_(file_idx, channel_idx)

    def get_channel_samples_count(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> int:
        """Get the number of samples in a channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Channel index.

        Returns:
            Number of samples.
        """
        callable_ = self._function_registry.get_function(
            "get_channel_samples_count"
        )
        return callable_(file_idx, channel_idx)

    def get_channel_samples(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> tuple[int, list[float], list[float]]:
        """Get all samples from a channel.

        The native API requires the caller to allocate the time and value
        buffers before calling the function.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Channel index.

        Returns:
            A tuple containing the native result code, sample times, and
            sample values.
        """
        count = self.get_channel_samples_count(
            file_idx,
            channel_idx,
        )

        if count <= 0:
            return count, [], []

        times = (ctypes.c_double * count)()
        values = (ctypes.c_double * count)()

        callable_ = self._function_registry.get_function(
            "get_channel_samples"
        )

        result = callable_(
            file_idx,
            channel_idx,
            times,
            values,
            count,
        )

        return result, list(times), list(values)

    def get_lap_channel_samples_count(
        self,
        file_idx: int,
        lap_idx: int,
        channel_idx: int,
    ) -> int:
        """Get the number of samples in a channel for a specific lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.
            channel_idx: Channel index.

        Returns:
            Number of samples.
        """
        callable_ = self._function_registry.get_function(
            "get_lap_channel_samples_count"
        )
        return callable_(
            file_idx,
            lap_idx,
            channel_idx,
        )

    def get_lap_channel_samples(
        self,
        file_idx: int,
        lap_idx: int,
        channel_idx: int,
    ) -> tuple[int, list[float], list[float]]:
        """Get channel samples for a specific lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.
            channel_idx: Channel index.

        Returns:
            A tuple containing the native result code, sample times, and
            sample values.
        """
        count = self.get_lap_channel_samples_count(
            file_idx,
            lap_idx,
            channel_idx,
        )

        if count <= 0:
            return count, [], []

        times = (ctypes.c_double * count)()
        values = (ctypes.c_double * count)()

        callable_ = self._function_registry.get_function(
            "get_lap_channel_samples"
        )

        result = callable_(
            file_idx,
            lap_idx,
            channel_idx,
            times,
            values,
            count,
        )

        return result, list(times), list(values)

    # ------------------------------------------------------------------
    # GPS functions
    # ------------------------------------------------------------------

    def set_gps_sample_frequency(self, frequency: float) -> int:
        """Set the GPS computation frequency.

        This must be called before accessing GPS channels.

        Args:
            frequency: Requested GPS frequency in Hz. The native API
                supports frequencies from 1 to 100 Hz.

        Returns:
            ``0`` on success, ``1`` if called too late, or ``2`` for an
            invalid frequency.
        """
        callable_ = self._function_registry.get_function(
            "set_GPS_sample_freq"
        )
        return callable_(frequency)

    def get_gps_channels_count(self, file_idx: int) -> int:
        """Get the number of computed GPS channels.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Number of GPS channels.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_channels_count"
        )
        return callable_(file_idx)

    def get_gps_channel_name(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get a GPS channel name.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: GPS channel index.

        Returns:
            GPS channel name, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_channel_name"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_channel_name_no_spaces(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get a GPS channel name without spaces.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: GPS channel index.

        Returns:
            GPS channel name without spaces.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_channel_name_no_spaces"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_channel_units(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get the units for a GPS channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: GPS channel index.

        Returns:
            GPS channel units, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_channel_units"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_channel_samples_count(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> int:
        """Get the number of samples in a GPS channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: GPS channel index.

        Returns:
            Number of GPS samples.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_channel_samples_count"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_channel_samples(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> tuple[int, list[float], list[float]]:
        """Get all samples from a GPS channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: GPS channel index.

        Returns:
            A tuple containing the native result code, sample times, and
            sample values.
        """
        count = self.get_gps_channel_samples_count(
            file_idx,
            channel_idx,
        )

        if count <= 0:
            return count, [], []

        times = (ctypes.c_double * count)()
        values = (ctypes.c_double * count)()

        callable_ = self._function_registry.get_function(
            "get_GPS_channel_samples"
        )

        result = callable_(
            file_idx,
            channel_idx,
            times,
            values,
            count,
        )

        return result, list(times), list(values)

    def get_lap_gps_channel_samples_count(
        self,
        file_idx: int,
        lap_idx: int,
        channel_idx: int,
    ) -> int:
        """Get GPS sample count for a specific lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.
            channel_idx: GPS channel index.

        Returns:
            Number of samples.
        """
        callable_ = self._function_registry.get_function(
            "get_lap_GPS_channel_samples_count"
        )
        return callable_(
            file_idx,
            lap_idx,
            channel_idx,
        )

    def get_lap_gps_channel_samples(
        self,
        file_idx: int,
        lap_idx: int,
        channel_idx: int,
    ) -> tuple[int, list[float], list[float]]:
        """Get GPS channel samples for a specific lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.
            channel_idx: GPS channel index.

        Returns:
            A tuple containing the native result code, sample times, and
            sample values.
        """
        count = self.get_lap_gps_channel_samples_count(
            file_idx,
            lap_idx,
            channel_idx,
        )

        if count <= 0:
            return count, [], []

        times = (ctypes.c_double * count)()
        values = (ctypes.c_double * count)()

        callable_ = self._function_registry.get_function(
            "get_lap_GPS_channel_samples"
        )

        result = callable_(
            file_idx,
            lap_idx,
            channel_idx,
            times,
            values,
            count,
        )

        return result, list(times), list(values)

    # ------------------------------------------------------------------
    # GPS raw channel functions
    # ------------------------------------------------------------------

    def get_gps_raw_channels_count(self, file_idx: int) -> int:
        """Get the number of raw GPS channels.

        Args:
            file_idx: Internal file index returned by ``open_file``.

        Returns:
            Number of raw GPS channels.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_raw_channels_count"
        )
        return callable_(file_idx)

    def get_gps_raw_channel_name(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get a raw GPS channel name.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Raw GPS channel index.

        Returns:
            Raw GPS channel name, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_raw_channel_name"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_raw_channel_name_no_spaces(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get a raw GPS channel name without spaces.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Raw GPS channel index.

        Returns:
            Raw GPS channel name without spaces.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_raw_channel_name_no_spaces"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_raw_channel_units(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> Optional[str]:
        """Get the units for a raw GPS channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Raw GPS channel index.

        Returns:
            Raw GPS channel units, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_raw_channel_units"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_raw_channel_samples_count(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> int:
        """Get the number of samples in a raw GPS channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Raw GPS channel index.

        Returns:
            Number of samples.
        """
        callable_ = self._function_registry.get_function(
            "get_GPS_raw_channel_samples_count"
        )
        return callable_(file_idx, channel_idx)

    def get_gps_raw_channel_samples(
        self,
        file_idx: int,
        channel_idx: int,
    ) -> tuple[int, list[float], list[float]]:
        """Get all samples from a raw GPS channel.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            channel_idx: Raw GPS channel index.

        Returns:
            A tuple containing the native result code, sample times, and
            sample values.
        """
        count = self.get_gps_raw_channel_samples_count(
            file_idx,
            channel_idx,
        )

        if count <= 0:
            return count, [], []

        times = (ctypes.c_double * count)()
        values = (ctypes.c_double * count)()

        callable_ = self._function_registry.get_function(
            "get_GPS_raw_channel_samples"
        )

        result = callable_(
            file_idx,
            channel_idx,
            times,
            values,
            count,
        )

        return result, list(times), list(values)

    def get_lap_gps_raw_channel_samples_count(
        self,
        file_idx: int,
        lap_idx: int,
        channel_idx: int,
    ) -> int:
        """Get raw GPS sample count for a specific lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.
            channel_idx: Raw GPS channel index.

        Returns:
            Number of samples.
        """
        callable_ = self._function_registry.get_function(
            "get_lap_GPS_raw_channel_samples_count"
        )
        return callable_(
            file_idx,
            lap_idx,
            channel_idx,
        )

    def get_lap_gps_raw_channel_samples(
        self,
        file_idx: int,
        lap_idx: int,
        channel_idx: int,
    ) -> tuple[int, list[float], list[float]]:
        """Get raw GPS samples for a specific lap.

        Args:
            file_idx: Internal file index returned by ``open_file``.
            lap_idx: Lap index.
            channel_idx: Raw GPS channel index.

        Returns:
            A tuple containing the native result code, sample times, and
            sample values.
        """
        count = self.get_lap_gps_raw_channel_samples_count(
            file_idx,
            lap_idx,
            channel_idx,
        )

        if count <= 0:
            return count, [], []

        times = (ctypes.c_double * count)()
        values = (ctypes.c_double * count)()

        callable_ = self._function_registry.get_function(
            "get_lap_GPS_raw_channel_samples"
        )

        result = callable_(
            file_idx,
            lap_idx,
            channel_idx,
            times,
            values,
            count,
        )

        return result, list(times), list(values)

    # ------------------------------------------------------------------
    # Library information
    # ------------------------------------------------------------------

    def get_library_date(self) -> Optional[str]:
        """Get the date on which the native library was compiled.

        Returns:
            Library compile date, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_library_date"
        )
        return callable_()

    def get_library_time(self) -> Optional[str]:
        """Get the time at which the native library was compiled.

        Returns:
            Library compile time, or ``None`` if unavailable.
        """
        callable_ = self._function_registry.get_function(
            "get_library_time"
        )
        return callable_()

    def library_test_on_open_files(self) -> Optional[str]:
        """Get a textual summary of currently open files.

        Returns:
            Textual summary returned by the native library, or ``None`` if
            unavailable.
        """
        callable_ = self._function_registry.get_function(
            "library_test_on_open_files"
        )
        return callable_()