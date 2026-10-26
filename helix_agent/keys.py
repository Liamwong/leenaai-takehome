"""Idempotency key recipes, one pure function per tool (CTX §4).

This is the only implementation of these recipes. The mocks and the tool
registry both import it, so the executor and the mock can never disagree
about what counts as "the same action".

Keys are scoped per tool by the idempotency store, so tools that share a
recipe (revoke_sessions and force_password_reset both use user + incident)
do not collide.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any


def canonical_json(value: Any) -> str:
    """Stable JSON: sorted keys, no whitespace, dates as ISO strings."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default
    )


def unlock_account(account: str, lock_epoch: datetime | int) -> str:
    """account + lock epoch. A new lockout of the same account is a new action."""
    return _join(_user(account), str(_epoch_seconds(lock_epoch)))


def send_password_reset(user: str, day: date) -> str:
    """user + UTC calendar day: at most one reset email per user per day."""
    return _join(_user(user), _day(day))


def create_request(user: str, item: str, day: date) -> str:
    """user + catalog item + UTC calendar day."""
    return _join(_user(user), _text(item, "item"), _day(day))


def grant_admin(user: str, session_id: str) -> str:
    """user + session. Session id = ticket id (our choice; noted in README)."""
    return _join(_user(user), _text(session_id, "session_id"))


def create_case(asset_id: str, case_type: str) -> str:
    """asset + case type (Lost/Stolen or offboarding)."""
    return _join(_text(asset_id, "asset_id"), _text(case_type, "case_type"))


def create_approval(requester: str, target: str, action: str, params: Mapping[str, Any]) -> str:
    """Request hash: sha256 over the exact action, so a re-file of the same
    request maps to the same approval and any change of parameters does not."""
    body = {
        "requester": _user(requester),
        "target": _user(target),
        "action": _text(action, "action"),
        "params": dict(params),
    }
    return hashlib.sha256(canonical_json(body).encode()).hexdigest()


def grant_access(approval_id: str) -> str:
    """AMBER: the approval id is the key, so one approval executes at most once."""
    return _text(approval_id, "approval_id")


def disable_mfa(approval_id: str) -> str:
    """AMBER: the approval id is the key."""
    return _text(approval_id, "approval_id")


def revoke_sessions(user: str, incident_id: str) -> str:
    """user + incident. Incident id = ticket id (CTX §9)."""
    return _join(_user(user), _text(incident_id, "incident_id"))


def force_password_reset(user: str, incident_id: str) -> str:
    """user + incident. Incident id = ticket id (CTX §9)."""
    return _join(_user(user), _text(incident_id, "incident_id"))


def open_incident(ticket_id: str) -> str:
    """ticket id: one incident per ticket."""
    return _text(ticket_id, "ticket_id")


def page_oncall(ticket_id: str) -> str:
    """ticket id: one page per ticket."""
    return _text(ticket_id, "ticket_id")


def _join(*parts: str) -> str:
    return "|".join(parts)


def _text(value: str, name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{name} must be non-empty")
    if "|" in cleaned:
        raise ValueError(f"{name} must not contain '|'")
    return cleaned


def _user(value: str) -> str:
    # Emails are case-insensitive, so Alice@ and alice@ are the same user.
    return _text(value, "user").lower()


def _day(day: date) -> str:
    if isinstance(day, datetime):
        raise TypeError("pass a date, not a datetime; use clock.utc_day()")
    return day.isoformat()


def _epoch_seconds(lock_epoch: datetime | int) -> int:
    if isinstance(lock_epoch, datetime):
        if lock_epoch.tzinfo is None:
            raise ValueError("lock_epoch must be timezone-aware")
        return int(lock_epoch.timestamp())
    if isinstance(lock_epoch, bool) or not isinstance(lock_epoch, int):
        raise TypeError("lock_epoch must be a datetime or int seconds")
    return lock_epoch


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"not JSON-serializable: {type(value).__name__}")
