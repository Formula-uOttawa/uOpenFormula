from dataclasses import dataclass

@dataclass(frozen=True)
class AimLap:
    id: int
    start: float
    duration: float

@dataclass(frozen=True)
class AimChannelMetadata:
    id: int
    name: str
    name_no_spaces: str
    unit: str

@dataclass(frozen=True)
class AimChannelSamples:
    timestamps: list[float]
    values: list[float]

@dataclass(frozen=True)
class AimChannel:
    metadata: AimChannelMetadata
    samples: AimChannelSamples

@dataclass(frozen=True)
class AimGPSChannel:
    metadata: AimChannelMetadata
    samples: AimChannelSamples