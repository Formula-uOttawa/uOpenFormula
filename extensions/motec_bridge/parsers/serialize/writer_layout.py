import struct
from typing import BinaryIO


class WriterLayout:

    _writer: BinaryIO

    def __init__(self, writer: BinaryIO):
        self._writer = writer

    def u8(self, value: int) -> None:
        self._writer.write(value.to_bytes(1, "little"))

    def u16(self, value: int) -> None:
        self._writer.write(value.to_bytes(2, "little"))

    def u32(self, value: int) -> None:
        self._writer.write(value.to_bytes(4, "little"))

    def utf8(self, value: str, size: int) -> None:
        string_bytes = self._encode_string(value, size)
        self._writer.write(string_bytes)

    def float_array(self, value: list[float]) -> None:
        self._writer.write(struct.pack(f"<{len(value)}f", *value))

    def bytes(self, value: bytes) -> None:
        self._writer.write(value)

    def pad(self, size: int) -> None:
        self._writer.write(bytes(size))

    def _encode_string(self, value, size):
        data = value.encode("utf-8")
        return data[:size].ljust(size, b"\x00")