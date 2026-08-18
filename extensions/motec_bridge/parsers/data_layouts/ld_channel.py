from dataclasses import dataclass


@dataclass
class LdChannel:
    meta_ptr: int
    prev_meta_ptr: int
    next_meta_ptr: int
    data_ptr: int
    data_len: int

    frequency: int
    shift: int
    mul: int
    scale: int
    dec: int
    name: str
    short_name: str
    unit: str

    data: list[float]
