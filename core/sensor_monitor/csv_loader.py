import csv
from pathlib import Path

def load_csv(file_path):
    path = Path(file_path).expanduser()

    # Read CSV records. The CSV library handles quoted values
    # and comments that span multiple lines.
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        records = list(csv.reader(file, strict=True))

    # AiM files contain session information before the measurements.
    # Their channel header starts with Time and has multiple channels.
    header_index = None

    for index, record in enumerate(records):
        if len(record) > 2 and record[0] == "Time":
            header_index = index
            break

    if header_index is None:
        raise ValueError(
            "Could not find the AiM channel header starting with Time."
        )

    channels = records[header_index]

    if len(set(channels)) != len(channels):
        raise ValueError("The CSV contains duplicate channel names.")

    if any(not channel.strip() for channel in channels):
        raise ValueError("The CSV contains a blank channel name.")

    # Store the session information above the channel header.
    metadata = {}

    for record in records[:header_index]:
        if len(record) >= 2:
            metadata[record[0]] = (
                record[1] if len(record) == 2 else record[1:]
            )

    # The next nonempty record contains the channel units.
    units_index = header_index + 1

    while units_index < len(records) and not records[units_index]:
        units_index += 1

    if units_index == len(records):
        raise ValueError("The CSV has no units row.")

    unit_values = records[units_index]

    if len(unit_values) != len(channels):
        raise ValueError("The units row does not match the channel count.")

    units = dict(zip(channels, unit_values))

    # Match each measurement value to its channel name.
    data = []

    for index, record in enumerate(
        records[units_index + 1:],
        start=units_index + 2,
    ):
        if not record:
            continue

        if len(record) != len(channels):
            raise ValueError(
                f"CSV record {index} has {len(record)} fields; "
                f"expected {len(channels)}."
            )

        data.append(dict(zip(channels, record)))

    if not data:
        raise ValueError("The CSV contains no measurement rows.")

    return {
        "source": str(path.resolve()),
        "metadata": metadata,
        "channels": channels,
        "units": units,
        "data": data,
    }