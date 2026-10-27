"""In-memory asset management: Lost/Stolen and offboarding return-kit cases (CTX §4)."""

from __future__ import annotations

from typing import Any

from helix_agent.clock import Clock
from helix_agent.mocks.core import InvalidArgument, MockService

CASE_TYPES = frozenset({"lost_stolen", "offboarding_return"})
INITIAL_STATE = "OPEN"


class AssetMgmtMock(MockService):
    def __init__(self, clock: Clock | None = None) -> None:
        super().__init__(clock)
        self.register("assetmgmt.create_case", self._create_case, mutating=True)

    def _create_case(self, args: dict[str, Any]) -> dict[str, Any]:
        case_type = args["case_type"]
        if case_type not in CASE_TYPES:
            raise InvalidArgument(f"unknown case_type: {case_type!r}")
        fields = dict(args.get("fields") or {})
        asset_id = fields.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise InvalidArgument("fields.asset_id is required")

        # The counter lives in _state, so a rolled-back call also rolls back its ID.
        number = (self._get("counter", "case") or {"n": 0})["n"] + 1
        self._put("counter", "case", {"n": number})
        case_id = f"CASE-{number:06d}"
        self._put(
            "case",
            case_id,
            {
                "id": case_id,
                "case_type": case_type,
                "asset_id": asset_id,
                # Optional. Whether a missing one needs ASK is the gate's call (CTX §8.3).
                "police_case_no": fields.get("police_case_no"),
                "state": INITIAL_STATE,
            },
        )
        return {"id": case_id, "state": INITIAL_STATE}
