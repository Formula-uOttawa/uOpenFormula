from dataclasses import dataclass


@dataclass
class LdLapInfo:
    total_laps: int
    fastest_time: float
    fastest_lap: int
