"""In-memory Okta: account lock, sessions, password, MFA factors and risk flags.

Mocks only validate arguments and record effects. Whether to unlock, reset or
disable MFA is decided by the safety gate, not here.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from helix_agent.clock import Clock
from helix_agent.mocks.core import InvalidArgument, MockService, UnknownEntity
from helix_agent.mocks.directory import email_args, normalize_email

RISK_FLAGS = ("compromise", "mfa_fatigue", "impossible_travel")


def _default_account() -> dict[str, Any]:
    return {
        "locked": False,
        "lock_epoch": None,
        "last_unlocked_epoch": None,
        "sessions_active": 0,
        "password_epoch": 0,
        "reset_sent_on": None,
        "resets_sent": [],
        "mfa_factors": [],
        "risk": dict.fromkeys(RISK_FLAGS, False),
    }


class OktaMock(MockService):
    def __init__(
        self, clock: Clock | None = None, accounts: Mapping[str, dict[str, Any]] | None = None
    ) -> None:
        super().__init__(clock)
        # Kept so reset() can restore the seed rather than leave no accounts.
        self._seed = copy.deepcopy(dict(accounts or {}))
        self._load(self._seed)
        # Every Okta tool takes a user email, so all of them normalize it the same way.
        user = email_args(("user",))
        self.register("okta.risk_signals", self._risk_signals, mutating=False, normalize=user)
        self.register("okta.unlock_account", self._unlock_account, mutating=True, normalize=user)
        self.register(
            "okta.send_password_reset", self._send_password_reset, mutating=True, normalize=user
        )
        self.register("okta.revoke_sessions", self._revoke_sessions, mutating=True, normalize=user)
        self.register(
            "okta.force_password_reset", self._force_password_reset, mutating=True, normalize=user
        )
        self.register("okta.disable_mfa", self._disable_mfa, mutating=True, normalize=user)

    def reset(self) -> None:
        super().reset()
        self._load(self._seed)

    # -- public, non-tool helpers --------------------------------------------

    def lock(self, user: str, epoch: int) -> None:
        """Re-lock an account at a new epoch. Test setup, not a tool."""
        account = self._account(user)
        account["locked"] = True
        account["lock_epoch"] = _int_arg(epoch, "lock_epoch")
        self._put("account", normalize_email(user), account)

    # -- tools -----------------------------------------------------------------

    def _risk_signals(self, args: dict[str, Any]) -> dict[str, Any]:
        account = self._account(args["user"])
        return {"user": normalize_email(args["user"]), **account["risk"]}

    def _unlock_account(self, args: dict[str, Any]) -> dict[str, Any]:
        # The key (account + lock epoch) makes a repeat of the same lockout a no-op.
        # Unlocking is always allowed here; the gate decides whether to call it.
        user = args["user"]
        epoch = _int_arg(args["lock_epoch"], "lock_epoch")
        account = self._account(user)
        account["locked"] = False
        account["last_unlocked_epoch"] = epoch
        self._put("account", normalize_email(user), account)
        return {"user": normalize_email(user), "locked": False, "last_unlocked_epoch": epoch}

    def _send_password_reset(self, args: dict[str, Any]) -> dict[str, Any]:
        user = args["user"]
        day = _day_arg(args["utc_date"])
        account = self._account(user)
        account["resets_sent"].append(day)
        account["reset_sent_on"] = day
        self._put("account", normalize_email(user), account)
        return {"user": normalize_email(user), "reset_sent_on": day}

    def _revoke_sessions(self, args: dict[str, Any]) -> dict[str, Any]:
        user = args["user"]
        account = self._account(user)
        account["sessions_active"] = 0
        self._put("account", normalize_email(user), account)
        return {"user": normalize_email(user), "sessions_active": 0}

    def _force_password_reset(self, args: dict[str, Any]) -> dict[str, Any]:
        user = args["user"]
        account = self._account(user)
        account["password_epoch"] += 1
        self._put("account", normalize_email(user), account)
        return {"user": normalize_email(user), "password_epoch": account["password_epoch"]}

    def _disable_mfa(self, args: dict[str, Any]) -> dict[str, Any]:
        # No approval check here: the AMBER gate (S3.3) checks the approval record.
        # The approval id is only the idempotency key (keys.disable_mfa).
        user = args["user"]
        account = self._account(user)
        account["mfa_factors"] = []
        self._put("account", normalize_email(user), account)
        return {"user": normalize_email(user), "mfa_factors": []}

    # -- internals -------------------------------------------------------------

    def _load(self, accounts: Mapping[str, dict[str, Any]]) -> None:
        for email, seed in accounts.items():
            account = _default_account() | {k: v for k, v in seed.items() if k != "risk"}
            account["risk"] = {**account["risk"], **seed.get("risk", {})}
            self._put("account", normalize_email(email), account)

    def _account(self, user: str) -> dict[str, Any]:
        """A deep copy of the stored account, so callers mutate and then _put it back."""
        account = self._get("account", normalize_email(user))
        if account is None:
            raise UnknownEntity(f"unknown account: {user}")
        return copy.deepcopy(account)


def _int_arg(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidArgument(f"{name} must be an int (seconds)")
    return value


def _day_arg(value: Any) -> str:
    # Trusts the caller's UTC date (CTX §9); it only checks the shape.
    if isinstance(value, datetime) or not isinstance(value, (date, str)):
        raise InvalidArgument("utc_date must be a date or ISO date string")
    try:
        return date.fromisoformat(
            value.isoformat() if isinstance(value, date) else value
        ).isoformat()
    except ValueError as exc:
        raise InvalidArgument(f"utc_date is not an ISO date: {value!r}") from exc
