"""In-memory ServiceNow request catalog. Filing a request never grants it (CTX §4)."""

from __future__ import annotations

from typing import Any

from helix_agent.clock import Clock
from helix_agent.mocks.core import InvalidArgument, MockService
from helix_agent.mocks.directory import email_args

ITEMS = frozenset({"Travel Exception", "USB Exception", "Software", "Peripheral Catalog"})
INITIAL_STATE = "SUBMITTED"
# No GRANTED state: the mock never grants, so a request can only be SUBMITTED.
REQUEST_STATES = frozenset({INITIAL_STATE})


class ServiceNowMock(MockService):
    def __init__(self, clock: Clock | None = None) -> None:
        super().__init__(clock)
        self.register(
            "servicenow.create_request",
            self._create_request,
            mutating=True,
            normalize=email_args(("fields", "requester")),
        )

    def _create_request(self, args: dict[str, Any]) -> dict[str, Any]:
        item = args["item"]
        if item not in ITEMS:
            raise InvalidArgument(f"unknown catalog item: {item!r}")
        fields = dict(args.get("fields") or {})
        requester = fields.get("requester")
        if not isinstance(requester, str) or not requester.strip():
            raise InvalidArgument("fields.requester is required")
        # The counter lives in _state, so a rolled-back call also rolls back its ID.
        number = (self._get("counter", "request") or {"n": 0})["n"] + 1
        self._put("counter", "request", {"n": number})
        request_id = f"REQ-{number:06d}"
        # Any "state" in fields is ignored: the mock sets the state itself.
        self._put(
            "request",
            request_id,
            {
                "id": request_id,
                "item": item,
                "requester": requester,
                "fields": fields,
                "state": INITIAL_STATE,
            },
        )
        return {"id": request_id, "item": item, "state": INITIAL_STATE}
