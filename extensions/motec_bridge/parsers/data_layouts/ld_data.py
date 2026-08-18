from dataclasses import dataclass

from .ld_beacon import LdBeacon
from .ld_channel import LdChannel
from .ld_head import LdHead
from .ld_lap_info import LdLapInfo


@dataclass
class LdData:
    head: LdHead
    channels: list[LdChannel]
    beacons: list[LdBeacon]
    lap_info: LdLapInfo
