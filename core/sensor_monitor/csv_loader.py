import csv
from pathlib import Path

def load_csv(file_path):
    path = Path(file_path).expanduser()
    metadata = {}
    data = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        # Count CSV records, including empty records. A quoted comment can
        # span several physical lines while remaining a single record.
        records = enumerate(csv.reader(file, strict=True), start=1)
        for _, record in records:
            if len(record) > 2 and record[0] == "Time":
                channels = record
                break
            if len(record) >= 2:
                metadata[record[0]] = record[1] if len(record) == 2 else record[1:]
        else:
            raise ValueError("Could not find the AiM channel header starting with Time.")

        if len(set(channels)) != len(channels):
            raise ValueError("The CSV contains duplicate channel names.")
        if any(not channel.strip() for channel in channels):
            raise ValueError("The CSV contains a blank channel name.")

        unit_values = next((record for _, record in records if record), None)
        if unit_values is None:
            raise ValueError("The CSV has no units row.")
        if len(unit_values) != len(channels):
            raise ValueError("The units row does not match the channel count.")
        units = dict(zip(channels, unit_values))

        for index, record in records:
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
