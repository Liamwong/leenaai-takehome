"""Read-only identity directory: who a user is, their manager, and their devices.

Every user-affecting action must check this first (CTX §4). Both tools are
registered read-only, so a write here is a bug and is rejected by the base class.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from helix_agent.clock import Clock
from helix_agent.mocks.core import InvalidArgument, MockService, Normalizer, UnknownEntity


def normalize_email(email: str) -> str:
    # Matches helix_agent.keys: emails are case-insensitive, so store and look up lower-case.
    return email.strip().lower()


def email_args(*paths: tuple[str, ...]) -> Normalizer:
    """Build a register(normalize=...) hook that lower-cases the email at each key path.

    A path like ("fields", "requester") walks nested dicts. A missing or non-string
    value is left alone so the handler's own validation still reports it.
    """

    def normalize(args: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(args)
        for path in paths:
            node: Any = out
            for key in path[:-1]:
                node = node.get(key) if isinstance(node, dict) else None
            leaf = path[-1]
            if isinstance(node, dict) and isinstance(node.get(leaf), str):
                node[leaf] = normalize_email(node[leaf])
        return out

    return normalize


class DirectoryMock(MockService):
    def __init__(
        self, clock: Clock | None = None, users: Mapping[str, dict[str, Any]] | None = None
    ) -> None:
        super().__init__(clock)
        # Kept so reset() can restore the seed rather than leave an empty directory.
        self._seed = copy.deepcopy(dict(users or {}))
        self._load(self._seed)
        self.register(
            "directory.lookup_user",
            self._lookup_user,
            mutating=False,
            normalize=email_args(("email",)),
        )
        self.register(
            "directory.verify_manager",
            self._verify_manager,
            mutating=False,
            normalize=email_args(("requester",), ("target",)),
        )

    def reset(self) -> None:
        super().reset()
        self._load(self._seed)

    # -- public, non-tool helpers ----------------------------------------------

    def owns_device(self, user: str, device_id: str) -> bool:
        record = self._get("user", normalize_email(user))
        return record is not None and device_id in record["devices"]

    # -- tools -------------------------------------------------------------------

    def _lookup_user(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._require_user(args["email"])

    def _verify_manager(self, args: dict[str, Any]) -> dict[str, Any]:
        requester = self._require_user(args["requester"])
        target = self._require_user(args["target"])
        if requester["email"] == target["email"]:
            relation = "self"
        elif target["manager_id"] == requester["email"]:
            relation = "manager"
        else:
            relation = "unrelated"
        return {"relation": relation, "target_manager": target["manager_id"]}

    # -- internals ---------------------------------------------------------------

    def _load(self, users: Mapping[str, dict[str, Any]]) -> None:
        for email, record in users.items():
            key = normalize_email(email)
            manager = record.get("manager_id")
            self._put(
                "user",
                key,
                {
                    "email": key,
                    "manager_id": normalize_email(manager) if manager else None,
                    "data_owner_of": [normalize_email(e) for e in record.get("data_owner_of", [])],
                    "tenant": record.get("tenant"),
                    "devices": list(record.get("devices", [])),
                },
            )

    def _require_user(self, email: str) -> dict[str, Any]:
        if not isinstance(email, str) or not email.strip():
            raise InvalidArgument("email must be a non-empty string")
        record = self._get("user", normalize_email(email))
        if record is None:
            raise UnknownEntity(f"unknown user: {email}")
        return copy.deepcopy(record)
