from io import TextIOWrapper
from typing import TextIO

from ..data_layouts.ld_lap_info import LdLapInfo


class LdLapInfoWriter:

    _ld_lap_info: LdLapInfo

    def __init__(self, ld_lap_info: LdLapInfo):
        self._ld_lap_info = ld_lap_info

    def write(self, writer: TextIO) -> None:
        total_laps = self._ld_lap_info.total_laps
        fastest_time = self._ld_lap_info.fastest_time
        fastest_lap = self._ld_lap_info.fastest_lap

        total_minutes = int(fastest_time // 60)
        seconds = int(fastest_time % 60)
        milliseconds = int((fastest_time - int(fastest_time)) * 1000)

        formatted_time = (
            f"{total_minutes}:{seconds:02d}.{milliseconds:03d}"
        )

        writer.write(
            f'  <Details>\n'
            f'   <String Id="Total Laps" Value="{total_laps}"/>\n'
            f'   <String Id="Fastest Time" Value="{formatted_time}"/>\n'
            f'   <String Id="Fastest Lap" Value="{fastest_lap}"/>\n'
            f'  </Details> \n'
        )