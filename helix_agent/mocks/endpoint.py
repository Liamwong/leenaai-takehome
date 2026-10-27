"""In-memory endpoint tool: temporary local admin on the user's own laptop (CTX §4, POL-04 §4.6)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from helix_agent.clock import Clock
from helix_agent.mocks.core import InvalidArgument, MockService, UnknownEntity
from helix_agent.mocks.directory import DirectoryMock, email_args

MAX_MINUTES = 60


class EndpointMock(MockService):
    def __init__(self, clock: Clock, directory: DirectoryMock) -> None:
        super().__init__(clock)
        # Ownership is checked against the directory, the source of truth for devices.
        self.directory = directory
        self.register(
            "endpoint.grant_admin",
            self._grant_admin,
            mutating=True,
            normalize=email_args(("user",)),
        )

    def _grant_admin(self, args: dict[str, Any]) -> dict[str, Any]:
        # args["user"] is already lower-case: call() applies the normalizer above.
        user = args["user"]
        device_id = args["device_id"]
        minutes = args["minutes"]
        # bool is a subclass of int, so it must be excluded explicitly.
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise InvalidArgument("minutes must be an int")
        if not 1 <= minutes <= MAX_MINUTES:
            raise InvalidArgument(f"minutes must be between 1 and {MAX_MINUTES}")
        # "No such user" and "not your laptop" are separate errors so the gate can tell them apart.
        if self.directory.read_state("user", user) is None:
            raise UnknownEntity(f"unknown user: {user}")
        if not self.directory.owns_device(user, device_id):
            raise InvalidArgument(f"device {device_id!r} is not owned by {user}")

        number = (self._get("counter", "grant") or {"n": 0})["n"] + 1
        self._put("counter", "grant", {"n": number})
        grant_id = f"GRANT-{number:06d}"
        expires_at = (self.clock.now() + timedelta(minutes=minutes)).isoformat()
        self._put(
            "admin_grant",
            grant_id,
            {
                "id": grant_id,
                "user": user,
                "device_id": device_id,
                "session_id": args["session_id"],
                "minutes": minutes,
                "expires_at": expires_at,
            },
        )
        return {"id": grant_id, "expires_at": expires_at}
