from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as date_parser


def _as_utc_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def parse_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return _as_utc_z(dt)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        if re.fullmatch(r"\d{14}", s):
            dt = datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            return _as_utc_z(dt)
        try:
            dt = date_parser.parse(s, dayfirst=True)
            return _as_utc_z(dt)
        except (ValueError, TypeError, OverflowError):
            return None
    return None
