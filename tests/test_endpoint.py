from datetime import UTC, datetime, timedelta

import pytest

from helix_agent import keys
from helix_agent.clock import FixedClock
from helix_agent.mocks import DirectoryMock, EndpointMock, InvalidArgument

T0 = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
ALICE = "alice@helix.example"
BOB = "bob@helix.example"
SESSION = "KAN-12"
KEY = keys.grant_admin(ALICE, SESSION)


@pytest.fixture
def endpoint():
    clock = FixedClock(T0)
    directory = DirectoryMock(
        clock=clock,
        users={
            ALICE: {"devices": ["LT-0001"]},
            BOB: {"devices": ["LT-0002"]},
        },
    )
    return EndpointMock(clock, directory)


def grant(endpoint, minutes=30, device_id="LT-0001", user=ALICE, key=KEY):
    args = {
        "user": user,
        "device_id": device_id,
        "minutes": minutes,
        "session_id": SESSION,
    }
    return endpoint.call("endpoint.grant_admin", args, key)


def assert_no_grant(endpoint):
    assert endpoint.snapshot()["state"].get("admin_grant", {}) == {}
    assert endpoint.read_state("admin_grant", "GRANT-000001") is None
    assert endpoint.replay_record("endpoint.grant_admin", KEY) is None


def test_tool_names_match_catalog(endpoint):
    assert endpoint.tools == frozenset({"endpoint.grant_admin"})


def test_61_minutes_raises_and_leaves_no_grant(endpoint):
    with pytest.raises(InvalidArgument):
        grant(endpoint, minutes=61)
    assert_no_grant(endpoint)


def test_device_user_does_not_own_raises_and_leaves_no_grant(endpoint):
    with pytest.raises(InvalidArgument):
        grant(endpoint, device_id="LT-0002")
    assert_no_grant(endpoint)


@pytest.mark.parametrize("minutes", [0, -5, True, "30", 30.0], ids=lambda m: repr(m))
def test_invalid_minutes_raise_and_leave_no_grant(endpoint, minutes):
    with pytest.raises(InvalidArgument):
        grant(endpoint, minutes=minutes)
    assert_no_grant(endpoint)


def test_sixty_minute_grant_expires_exactly_sixty_minutes_later(endpoint):
    result = grant(endpoint, minutes=60)
    expected = (T0 + timedelta(minutes=60)).isoformat()
    assert result["expires_at"] == expected
    stored = endpoint.read_state("admin_grant", result["id"])
    assert stored["expires_at"] == expected
    assert stored["device_id"] == "LT-0001"


def test_rejected_call_does_not_consume_a_grant_id(endpoint):
    with pytest.raises(InvalidArgument):
        grant(endpoint, minutes=61)
    assert grant(endpoint, minutes=10)["id"] == "GRANT-000001"


def test_repeat_key_returns_same_grant(endpoint):
    assert grant(endpoint) == grant(endpoint)
    assert len(endpoint.snapshot()["state"]["admin_grant"]) == 1
