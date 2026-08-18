from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class LdHead:
    driver: str
    vehicle_id: str
    venue: str
    date: datetime
    short_comment: str
    session: str
