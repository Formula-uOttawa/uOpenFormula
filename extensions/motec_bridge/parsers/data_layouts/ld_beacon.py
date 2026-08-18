from dataclasses import dataclass


@dataclass
class LdBeacon:
    marker_version: int
    class_name: str
    name: str
    flags: int
    time: float