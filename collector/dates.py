from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dateutil import parser as date_parser


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_published(raw: str | None, default_timezone: str | None) -> tuple[str | None, int, str]:
    if not raw or not str(raw).strip():
        return None, 0, "unknown"
    text = str(raw).strip()
    try:
        parsed = date_parser.parse(text)
    except (TypeError, ValueError, OverflowError):
        return None, 0, "unknown"
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        return iso_utc(parsed), 3, "known"
    if default_timezone:
        try:
            parsed = parsed.replace(tzinfo=ZoneInfo(default_timezone))
            return iso_utc(parsed), 1, "known"
        except Exception:
            pass
    return None, 0, "unknown"


def local_date(iso_value: str | None, tz_name: str = "Asia/Shanghai") -> str | None:
    if not iso_value:
        return None
    try:
        return datetime.fromisoformat(iso_value.replace("Z", "+00:00")).astimezone(ZoneInfo(tz_name)).date().isoformat()
    except ValueError:
        return None
