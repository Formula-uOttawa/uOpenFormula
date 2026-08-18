from typing import TextIO

from parsers.data_layouts.ld_beacon import LdBeacon


class LdBeaconWriter:

    _ld_beacon: LdBeacon

    def __init__(self, ld_beacon: LdBeacon):
        self._ld_beacon = ld_beacon

    def write(self, writer: TextIO) -> None:
        scientific_notation = f"{self._ld_beacon.time * 1_000_000:.17E}"

        writer.write(
            f'     <Marker Version="{self._ld_beacon.marker_version}" '
            f'ClassName="{self._ld_beacon.class_name}" '
            f'Name="{self._ld_beacon.name}" '
            f'Flags="{self._ld_beacon.flags}" '
            f'Time="{scientific_notation}"/>\n'
        )