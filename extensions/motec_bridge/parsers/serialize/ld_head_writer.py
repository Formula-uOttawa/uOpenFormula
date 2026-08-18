from typing import BinaryIO

from parsers.data_layouts.ld_head import LdHead
from parsers.serialize.magic_numbers import (
    CHANNEL_META_PTR,
    EVENT_PTR,
    DEVICE_SERIAL,
    DEVICE_VERSION,
    MAX_STRING_SIZE,
    MAX_COMMENT_SIZE,
    HEADER_CONST_DATA
)
from parsers.serialize.writer_layout import WriterLayout

class LdHeadWriter:

    _ld_head: LdHead
    _channel_data_prt: int
    _n_channels: int

    def __init__(
            self,
            ld_head: LdHead,
            channel_data_prt: int,
            n_channels: int
    ):
        self._ld_head = ld_head
        self._channel_data_prt = channel_data_prt
        self._n_channels = n_channels

    @property
    def _date_string(self) -> str:

        year = self._ld_head.date.year
        month = self._ld_head.date.month
        day = self._ld_head.date.day


        return f"{day:02d}/{month:02d}/{year}"

    @property
    def _time_string(self) -> str:

        hour = self._ld_head.date.hour
        minute = self._ld_head.date.minute
        second = self._ld_head.date.second

        return f"{hour:02d}:{minute:02d}:{second:02d}"

    @property
    def _device_type_(self) -> str:
        return "ADL"

    @property
    def _header_const_data(self) -> bytes:
        return bytes(HEADER_CONST_DATA)

    @property
    def _other_info_placeholder(self) -> str:
        return "placeholder"


    def write(self, writer: BinaryIO) -> None:

        # File header
        writer.write(self._header_const_data)
        writer.seek(0)

        layout = WriterLayout(writer)
        # MoTeC header / metadata
        layout.u8(0x40)
        layout.pad(4)

        layout.u32(CHANNEL_META_PTR)
        layout.u32(self._channel_data_prt)
        layout.pad(20)

        layout.u32(EVENT_PTR)
        layout.pad(24)

        layout.u16(0x0000)
        layout.u16(0x4240)
        layout.u16(0x000F)

        # Device information
        layout.u32(DEVICE_SERIAL)
        layout.utf8(self._device_type_, 8)
        layout.u32(DEVICE_VERSION)

        layout.u16(0x0080)
        layout.u32(self._n_channels)
        layout.u32(0x0001_0064)

        # Session date/time
        layout.utf8(self._date_string, 16)
        layout.pad(16)

        layout.utf8(self._time_string, 16)
        layout.pad(16)

        # Session identification
        layout.utf8(self._ld_head.driver, MAX_STRING_SIZE)
        layout.utf8(self._ld_head.vehicle_id, MAX_STRING_SIZE)
        layout.pad(64)

        layout.utf8(self._ld_head.venue, MAX_STRING_SIZE)
        layout.pad(64)

        layout.utf8(self._other_info_placeholder, MAX_COMMENT_SIZE)

        # Session metadata
        layout.u32(0xD20822)
        layout.pad(2)

        layout.utf8(self._ld_head.session, MAX_STRING_SIZE)
        layout.utf8(self._ld_head.short_comment, MAX_STRING_SIZE)

        # Remaining header data
        layout.pad(8)
        layout.u8(99)
        layout.pad(117)

        # Channel/event data begins here.
        writer.seek(EVENT_PTR)