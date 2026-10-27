from datetime import UTC, datetime

import pytest

from helix_agent.clock import FixedClock
from helix_agent.mocks import DirectoryMock, InvalidArgument, UnknownEntity

T0 = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)

ALICE = "alice@helix.example"
BOB = "bob@helix.example"  # Alice's manager
CAROL = "carol@helix.example"  # reports to Bob too, so she is unrelated to Alice

SEED = {
    ALICE: {"manager_id": BOB, "tenant": "helix", "devices": ["LT-0001"]},
    BOB: {"tenant": "helix", "devices": ["LT-0002"]},
    CAROL: {"manager_id": BOB, "tenant": "helix", "devices": []},
}


@pytest.fixture
def directory():
    return DirectoryMock(clock=FixedClock(T0), users=SEED)


def test_lookup_user_returns_seeded_manager(directory):
    record = directory.call("directory.lookup_user", {"email": ALICE})
    assert record["manager_id"] == BOB
    assert record["devices"] == ["LT-0001"]


def test_lookup_user_is_case_insensitive(directory):
    record = directory.call("directory.lookup_user", {"email": "ALICE@Helix.example "})
    assert record["email"] == ALICE


def test_lookup_unknown_email_raises(directory):
    with pytest.raises(UnknownEntity):
        directory.call("directory.lookup_user", {"email": "nobody@helix.example"})


def test_blank_email_is_invalid_argument(directory):
    with pytest.raises(InvalidArgument):
        directory.call("directory.lookup_user", {"email": "  "})


@pytest.mark.parametrize(
    "requester, relation",
    [(ALICE, "self"), (BOB, "manager"), (CAROL, "unrelated")],
    ids=["self", "manager", "unrelated"],
)
def test_verify_manager_relations(directory, requester, relation):
    result = directory.call("directory.verify_manager", {"requester": requester, "target": ALICE})
    assert result == {"relation": relation, "target_manager": BOB}


def test_verify_manager_unknown_requester_raises(directory):
    with pytest.raises(UnknownEntity):
        directory.call(
            "directory.verify_manager", {"requester": "ghost@helix.example", "target": ALICE}
        )


def test_directory_tools_are_read_only(directory):
    # No key is passed, so these must not need one, and must leave state untouched.
    before = directory.snapshot()
    directory.call("directory.lookup_user", {"email": ALICE})
    directory.call("directory.verify_manager", {"requester": BOB, "target": ALICE})
    assert directory.snapshot() == before
    assert directory.replay_record("directory.lookup_user", "anything") is None


def test_tool_names_match_catalog(directory):
    assert directory.tools == frozenset({"directory.lookup_user", "directory.verify_manager"})


def test_owns_device_only_for_own_devices(directory):
    assert directory.owns_device(ALICE, "LT-0001") is True
    assert directory.owns_device(ALICE, "LT-0002") is False
    assert directory.owns_device("ALICE@helix.example", "LT-0001") is True


def test_owns_device_unknown_user_is_false(directory):
    assert directory.owns_device("ghost@helix.example", "LT-0001") is False


def test_reset_restores_seed(directory):
    directory.reset()
    assert directory.call("directory.lookup_user", {"email": BOB})["email"] == BOB
