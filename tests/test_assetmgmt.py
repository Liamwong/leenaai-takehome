from datetime import UTC, datetime

import pytest

from helix_agent import keys
from helix_agent.clock import FixedClock
from helix_agent.mocks import AssetMgmtMock, InvalidArgument, ReplayConflict

T0 = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
ASSET = "LT-0042"


@pytest.fixture
def assets():
    return AssetMgmtMock(clock=FixedClock(T0))


def create(assets, case_type="lost_stolen", extra=None, key=None):
    fields = {"asset_id": ASSET, **(extra or {})}
    key = key or keys.create_case(ASSET, case_type)
    return assets.call("assetmgmt.create_case", {"case_type": case_type, "fields": fields}, key)


def test_tool_names_match_catalog(assets):
    assert assets.tools == frozenset({"assetmgmt.create_case"})


def test_same_asset_and_type_returns_existing_case(assets):
    first = create(assets)
    second = create(assets)
    assert first["id"] == second["id"]
    assert first["state"] == "OPEN"
    assert len(assets.snapshot()["state"]["case"]) == 1


def test_offboarding_return_case_is_accepted(assets):
    result = create(assets, case_type="offboarding_return")
    assert assets.read_state("case", result["id"])["case_type"] == "offboarding_return"


def test_bad_case_type_raises_and_stores_nothing(assets):
    with pytest.raises(InvalidArgument):
        create(assets, case_type="theft")
    assert assets.snapshot()["state"] == {}


def test_missing_asset_id_raises_and_stores_nothing(assets):
    with pytest.raises(InvalidArgument):
        assets.call(
            "assetmgmt.create_case",
            {"case_type": "lost_stolen", "fields": {}},
            "k1",
        )
    assert assets.snapshot()["state"] == {}


def test_police_case_no_is_stored_when_given(assets):
    result = create(assets, extra={"police_case_no": "PD-2026-881"})
    assert assets.read_state("case", result["id"])["police_case_no"] == "PD-2026-881"


def test_police_case_no_defaults_to_none(assets):
    result = create(assets)
    assert assets.read_state("case", result["id"])["police_case_no"] is None


def test_adding_police_case_no_on_replay_is_a_conflict(assets):
    # Decision (2026-10-26): same key + different args raises ReplayConflict.
    first = create(assets)
    with pytest.raises(ReplayConflict):
        create(assets, extra={"police_case_no": "PD-2026-881"})
    assert assets.read_state("case", first["id"])["police_case_no"] is None
