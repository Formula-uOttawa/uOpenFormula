from typing import BinaryIO

from parsers.data_layouts.ld_channel import LdChannel
from parsers.serialize.magic_numbers import MAGIC_SIZE, MAGIC_TYPE
from parsers.serialize.writer_layout import WriterLayout


class LdChannelWriter:

    _ld_channel: LdChannel
    _channel_number: int

    def __init__(
            self,
            ld_channel: LdChannel,
            channel_number: int
    ):
        self._ld_channel = ld_channel
        self._channel_number = channel_number

    def write(self, writer: BinaryIO):

        writer.seek(self._ld_channel.meta_ptr)

        layout = WriterLayout(writer)

        layout.u32(self._ld_channel.prev_meta_ptr)
        layout.u32(self._ld_channel.next_meta_ptr)
        layout.u32(self._ld_channel.data_ptr)
        layout.u32(self._ld_channel.data_len)

        layout.u16(4)
        layout.u16(MAGIC_TYPE)
        layout.u16(MAGIC_SIZE)

        layout.u16(self._ld_channel.frequency)
        layout.u16(self._ld_channel.shift)
        layout.u16(self._ld_channel.mul)
        layout.u16(self._ld_channel.scale)
        layout.u16(self._ld_channel.dec)

        layout.utf8(self._ld_channel.name, 32)
        layout.utf8(self._ld_channel.short_name, 8)
        layout.utf8(self._ld_channel.unit, 12)

        layout.u8(201)
        layout.pad(39)

