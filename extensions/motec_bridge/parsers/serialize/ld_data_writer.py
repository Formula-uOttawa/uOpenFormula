from parsers.data_layouts.ld_data import LdData
from parsers.serialize.ld_beacon_writer import LdBeaconWriter
from parsers.serialize.ld_channel_writer import LdChannelWriter
from parsers.serialize.ld_head_writer import LdHeadWriter
from parsers.serialize.ld_lap_info_writer import LdLapInfoWriter
from parsers.serialize.magic_numbers import HEADER_PTR
from parsers.serialize.writer_layout import WriterLayout


class LdDataWriter:

    _ld_data: LdData
    _channel_count: int
    _channel_data_ptr: int

    def __init__(self, ld_data: LdData):
        self._ld_data = ld_data
        self._channel_count = len(self._ld_data.channels)
        self._prepare_pointers()


    def _prepare_pointers(self):

        meta_offset = 0
        feta_offset = self._channel_count * 124
        sample_offset = 0

        meta_addresses: list[int] = []
        sample_byte_sizes: list[int] = []
        sample_addresses: list[int] = []

        # calculate addresses
        for idx, channel in enumerate(self._ld_data.channels):

            meta_addresses.append(HEADER_PTR + meta_offset)
            sample_addresses.append(HEADER_PTR + feta_offset + sample_offset)

            sample_byte_size = len(channel.data) * 4
            sample_byte_sizes.append(sample_byte_size)

            meta_offset += 124
            sample_offset += sample_byte_size

        # assign address to channels
        for idx, channel in enumerate(self._ld_data.channels):

            channel.prev_meta_ptr = 0 if idx == 0 else meta_addresses[idx - 1]
            channel.next_meta_ptr = 0 if idx == self._channel_count - 1 else meta_addresses[idx + 1]

            channel.data_len = len(channel.data)
            channel.data_ptr = sample_addresses[idx]

            channel.data_ptr = sample_addresses[idx]
            channel.meta_ptr = meta_addresses[idx]

        self._channel_data_ptr = sample_addresses[0]


    def save_logs(
            self,
            log_file_path: str,
            extension_file_path: str
    ) -> None:

        with open(log_file_path, "wb") as log_file:


            # write head
            head_writer = LdHeadWriter(
                self._ld_data.head,
                self._channel_data_ptr,
                self._channel_count
            )
            head_writer.write(log_file)

            # write channels
            for channel_number, channel in enumerate(self._ld_data.channels):
                channel_writer = LdChannelWriter(channel, channel_number)
                channel_writer.write(log_file)

            # write channel data
            for channel_number, channel in enumerate(self._ld_data.channels):
                log_file.seek(channel.data_ptr)
                layout = WriterLayout(log_file)
                layout.float_array(channel.data)

        with open(extension_file_path, "w") as extension_file:
            xml_header = "<?xml version=\"1.0\"?>\n<LDXFile Locale=\"English_Canada.1252\" DefaultLocale=\"C\" Version=\"1.6\">\n <Layers>\n  <Layer>\n   <MarkerBlock>\n    <MarkerGroup Name=\"Beacons\" Index=\"3\">"
            extension_file.write(xml_header)

            for beacon_number, beacon in enumerate(self._ld_data.beacons):
                beacon_writer = LdBeaconWriter(beacon)
                beacon_writer.write(extension_file)

            xml_separator = "    </MarkerGroup>\n   </MarkerBlock>\n   <RangeBlock/>\n  </Layer>"
            extension_file.write(xml_separator)

            lap_info_writer = LdLapInfoWriter(self._ld_data.lap_info)
            lap_info_writer.write(extension_file)

            xml_footer = "</Layers>\n</LDXFile>"
            extension_file.write(xml_footer)
