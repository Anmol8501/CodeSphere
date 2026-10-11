"""Calendar days in the application timezone (settings.APP_TIMEZONE).

Timestamps are stored in UTC. Every "day" CodeArena shows or counts (streaks,
the heatmap, "today", date filters) is a calendar day in ONE application
timezone, so every student, server and browser agrees on what "today" is.
The browser's timezone and the server's local timezone are never used.
"""

import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, literal_column
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.config import settings

_ZONE_NAME = re.compile(r"^[A-Za-z0-9_+\-/]+$")


def app_zone() -> ZoneInfo:
    return ZoneInfo(settings.APP_TIMEZONE)


def now_utc() -> datetime:
    return datetime.now(UTC)


def to_utc(value: datetime) -> datetime:
    """Aware UTC datetime (SQLite returns naive values that are already UTC)."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def local_today(now: datetime | None = None) -> date:
    return to_utc(now or now_utc()).astimezone(app_zone()).date()


def start_of_day_utc(day: date) -> datetime:
    """The UTC instant at which `day` begins in the application timezone."""
    return datetime.combine(day, time.min, tzinfo=app_zone()).astimezone(UTC)


def as_date(value) -> date:
    """A date from a DB value (PostgreSQL returns date, SQLite an ISO string)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def local_date_expr(db: Session, column) -> ColumnElement:
    """SQL expression for the calendar date of a UTC timestamp `column` in the app timezone.

    Rendered as a literal (not a bind parameter) so the same expression can be
    used in SELECT and GROUP BY.
    """
    if db.get_bind().dialect.name == "postgresql":
        name = settings.APP_TIMEZONE
        if not _ZONE_NAME.match(name):  # validated at startup; belt and braces
            raise ValueError("Invalid APP_TIMEZONE")
        return func.date(func.timezone(literal_column(f"'{name}'"), column))
    # SQLite (tests only) has no timezone support: shift by the zone's current
    # UTC offset, which is exact for zones without daylight saving time.
    offset = datetime.now(app_zone()).utcoffset() or timedelta(0)
    minutes = int(offset.total_seconds() // 60)
    return func.date(column, literal_column(f"'{minutes:+d} minutes'"))
