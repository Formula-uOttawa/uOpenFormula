import json
import os
from datetime import UTC, datetime
from pathlib import Path

from core.StatefulView import StatefulView

# for the versioning of the saving algorithm, so that backwards compatibility could be added in theory
SAVE_VERSION = 1

def save_project(path: str | Path, views: dict[str, StatefulView], **kwargs):
    # append .uof extension if not there already
    path = Path(path).with_suffix(".uof")

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    created = now
    if path.exists():
        try:
            with open(path, "r") as f:
                created = json.load(f).get("created", now)
        except (json.JSONDecodeError, OSError):
            pass


    save_info: dict = {
        "version": SAVE_VERSION,
        "created": created,
        "last_saved": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "views_info": {name: v.export_state() for (name, v) in views.items()},
        "extra": kwargs # allow function caller to pass any additional save info
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(save_info, f, indent=4)
    os.replace(tmp, path)

    for v in views.values():
        v.mark_state_saved()