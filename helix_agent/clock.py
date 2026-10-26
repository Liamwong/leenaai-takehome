"""Injectable UTC clock, so calendar days and lock epochs are deterministic in tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Current time as a timezone-aware UTC datetime."""
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """A clock that only moves when told to."""

    def __init__(self, at: datetime) -> None:
        self._at = _require_aware(at)

    def now(self) -> datetime:
        return self._at

    def set(self, at: datetime) -> None:
        self._at = _require_aware(at)

    def advance(self, **delta: float) -> None:
        self._at += timedelta(**delta)


def utc_day(at: datetime) -> date:
    """The UTC calendar day of an instant (CTX §9: calendar day = UTC date)."""
    return _require_aware(at).astimezone(UTC).date()


def _require_aware(at: datetime) -> datetime:
    if at.tzinfo is None:
        raise ValueError("naive datetime; pass a timezone-aware UTC datetime")
    return at
