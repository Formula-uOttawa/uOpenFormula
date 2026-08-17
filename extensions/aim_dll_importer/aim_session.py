from typing import Optional

from .aim_file import AimFile
from .aim_file_context_manager import AimFileContextManager
from .aim_types import AimLap, AimChannel, AimGPSChannel


class AimSession:
    _file: AimFile
    _context_manager: AimFileContextManager

    _logger_id: Optional[int]
    _devices: Optional[list[int]]
    _vehicle_name: Optional[str]
    _track_name: Optional[str]
    _racer_name: Optional[str]
    _championship_name: Optional[str]
    _session_type_name: Optional[str]
    _laps: Optional[list[AimLap]]
    _channels: Optional[list[AimChannel]]
    _gps_channels: Optional[list[AimGPSChannel]]

    def __init__(
        self,
        file: AimFile,
        context_manager: AimFileContextManager,
    ):
        self._file = file
        self._context_manager = context_manager

        self._logger_id = None
        self._devices = None
        self._vehicle_name = None
        self._track_name = None
        self._championship_name = None
        self._session_type_name = None
        self._racer_name = None
        self._laps = None
        self._channels = None
        self._gps_channels = None

    @property
    def logger_id(self) -> int:
        """Return the ID of the logger that recorded the session.

        Returns
        -------
        int
            The logger ID associated with the session.
        """
        if self._logger_id is None:
            self._logger_id = self._context_manager.get_logger_id(self._file)

        return self._logger_id

    @property
    def devices(self) -> list[int]:
        """Return the devices associated with the session.

        Returns
        -------
        list[int]
            A list of device IDs associated with the session.
        """
        if self._devices is None:
            self._devices = self._context_manager.get_devices(self._file)
        return self._devices

    @property
    def vehicle_name(self) -> str:
        """Return the name of the vehicle used in the session.

        Returns
        -------
        str
            The vehicle name.
        """
        if self._vehicle_name is None:
            self._vehicle_name = self._context_manager.get_vehicle_name(self._file)
        return self._vehicle_name

    @property
    def track_name(self) -> str:
        """Return the name of the track where the session took place.

        Returns
        -------
        str
            The track name.
        """
        if self._track_name is None:
            self._track_name = self._context_manager.get_track_name(self._file)
        return self._track_name

    @property
    def racer_name(self) -> str:
        """Return the name of the racer associated with the session.

        Returns
        -------
        str
            The racer name.
        """
        if self._racer_name is None:
            self._racer_name = self._context_manager.get_racer_name(self._file)
        return self._racer_name

    @property
    def championship_name(self) -> str:
        """Return the name of the championship associated with the session.

        Returns
        -------
        str
            The championship name.
        """
        if self._championship_name is None:
            self._championship_name = self._context_manager.get_championship_name(
                self._file
            )
        return self._championship_name

    @property
    def session_type_name(self) -> str:
        """Return the type of the session.

        Returns
        -------
        str
            The session type name, such as a practice, qualifying, or race
            session.
        """
        if self._session_type_name is None:
            self._session_type_name = self._context_manager.get_session_type_name(
                self._file
            )
        return self._session_type_name

    @property
    def laps(self) -> list[AimLap]:
        """Return all laps recorded in the session.

        Returns
        -------
        list[AimLap]
            A list containing the laps recorded in the session.
        """
        if self._laps is None:
            self._laps = self._context_manager.get_laps(self._file)
        return self._laps

    @property
    def channels(self) -> list[AimChannel]:
        """Return all data channels recorded in the session.

        Returns
        -------
        list[AimChannel]
            A list containing the data channels available in the session.
        """
        if self._channels is None:
            self._channels = self._context_manager.get_channels(self._file)
        return self._channels

    @property
    def gps_channels(self) -> list[AimGPSChannel]:
        """Return all GPS channels recorded in the session.

        Returns
        -------
        list[AimGPSChannel]
            A list containing the GPS channels available in the session.
        """
        if self._gps_channels is None:
            self._gps_channels = self._context_manager.get_gps_channels(self._file)
        return self._gps_channels

    def get_channels_by_lap(self, lap: AimLap) -> list[AimChannel]:
        """Return data channels for a specific lap.

        Parameters
        ----------
        lap : AimLap
            The lap for which data channels should be retrieved.

        Returns
        -------
        list[AimChannel]
            A list containing the data channels recorded during the
            specified lap.
        """
        return self._context_manager.get_channels(self._file, lap)

    def get_gps_channels_by_lap(self, lap: AimLap) -> list[AimGPSChannel]:
        """Return GPS channels for a specific lap.

        Parameters
        ----------
        lap : AimLap
            The lap for which GPS channels should be retrieved.

        Returns
        -------
        list[AimGPSChannel]
            A list containing the GPS channels recorded during the
            specified lap.
        """
        return self._context_manager.get_gps_channels(self._file, lap)