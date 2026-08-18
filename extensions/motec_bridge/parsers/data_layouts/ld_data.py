from dataclasses import dataclass

from parsers.data_layouts.ld_beacon import LdBeacon
from parsers.data_layouts.ld_channel import LdChannel
from parsers.data_layouts.ld_head import LdHead
from parsers.data_layouts.ld_lap_info import LdLapInfo


@dataclass
class LdData:
    head: LdHead
    channels: list[LdChannel]
    beacons: list[LdBeacon]
    lap_info: LdLapInfo
