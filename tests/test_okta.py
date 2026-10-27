from datetime import UTC, datetime

import pytest

from helix_agent import keys
from helix_agent.clock import FixedClock, utc_day
from helix_agent.mocks import InvalidArgument, OktaMock, UnknownEntity

T0 = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
LOCK_E1 = int(datetime(2026, 10, 26, 9, 30, tzinfo=UTC).timestamp())
LOCK_E2 = int(datetime(2026, 10, 26, 11, 0, tzinfo=UTC).timestamp())

ALICE = "alice@helix.example"
BOB = "bob@helix.example"


@pytest.fixture
def okta():
    return OktaMock(
        clock=FixedClock(T0),
        accounts={
            ALICE: {
                "locked": True,
                "lock_epoch": LOCK_E1,
                "sessions_active": 3,
                "mfa_factors": ["push", "totp"],
                "risk": {"compromise": True, "mfa_fatigue": False, "impossible_travel": True},
            },
            BOB: {"locked": False, "sessions_active": 1, "mfa_factors": ["push"]},
        },
    )


def read(okta, user=ALICE):
    return okta.read_state("account", user)


def test_tool_names_match_catalog(okta):
    assert okta.tools == frozenset(
        {
            "okta.risk_signals",
            "okta.unlock_account",
            "okta.send_password_reset",
            "okta.revoke_sessions",
            "okta.force_password_reset",
            "okta.disable_mfa",
        }
    )


def test_risk_signals_return_seeded_flags_without_key(okta):
    assert okta.call("okta.risk_signals", {"user": ALICE}) == {
        "user": ALICE,
        "compromise": True,
        "mfa_fatigue": False,
        "impossible_travel": True,
    }
    assert okta.call("okta.risk_signals", {"user": BOB})["compromise"] is False


def test_risk_signals_unknown_user_raises(okta):
    with pytest.raises(UnknownEntity):
        okta.call("okta.risk_signals", {"user": "ghost@helix.example"})


def test_repeat_unlock_same_key_and_epoch_is_identical_and_unlocks_once(okta):
    key = keys.unlock_account(ALICE, LOCK_E1)
    first = okta.call("okta.unlock_account", {"user": ALICE, "lock_epoch": LOCK_E1}, key)
    second = okta.call("okta.unlock_account", {"user": ALICE, "lock_epoch": LOCK_E1}, key)
    assert first == second
    assert read(okta)["locked"] is False
    assert read(okta)["last_unlocked_epoch"] == LOCK_E1

    # Re-lock at the same epoch. A replay must not unlock again, so it stays locked.
    okta.lock(ALICE, LOCK_E1)
    okta.call("okta.unlock_account", {"user": ALICE, "lock_epoch": LOCK_E1}, key)
    assert read(okta)["locked"] is True


def test_mixed_case_unlock_retry_with_same_key_is_a_replay(okta):
    key = keys.unlock_account(ALICE, LOCK_E1)
    first = okta.call("okta.unlock_account", {"user": ALICE, "lock_epoch": LOCK_E1}, key)
    second = okta.call(
        "okta.unlock_account", {"user": "Alice@Helix.Example", "lock_epoch": LOCK_E1}, key
    )
    assert first == second == {"user": ALICE, "locked": False, "last_unlocked_epoch": LOCK_E1}
    # Re-lock, then replay with mixed case. The handler must not run again, so it stays locked.
    okta.lock(ALICE, LOCK_E1)
    okta.call("okta.unlock_account", {"user": "ALICE@helix.example", "lock_epoch": LOCK_E1}, key)
    assert read(okta)["locked"] is True


def test_relock_with_new_epoch_unlocks_again(okta):
    okta.call(
        "okta.unlock_account",
        {"user": ALICE, "lock_epoch": LOCK_E1},
        keys.unlock_account(ALICE, LOCK_E1),
    )
    okta.lock(ALICE, LOCK_E2)
    assert read(okta)["locked"] is True

    okta.call(
        "okta.unlock_account",
        {"user": ALICE, "lock_epoch": LOCK_E2},
        keys.unlock_account(ALICE, LOCK_E2),
    )
    assert read(okta)["locked"] is False
    assert read(okta)["last_unlocked_epoch"] == LOCK_E2


def test_unlock_rejects_non_int_epoch(okta):
    with pytest.raises(InvalidArgument):
        okta.call("okta.unlock_account", {"user": ALICE, "lock_epoch": "1729"}, "k1")
    with pytest.raises(InvalidArgument):
        okta.call("okta.unlock_account", {"user": ALICE, "lock_epoch": True}, "k2")
    assert read(okta)["locked"] is True


def test_unlock_unknown_user_raises(okta):
    with pytest.raises(UnknownEntity):
        okta.call(
            "okta.unlock_account", {"user": "ghost@helix.example", "lock_epoch": LOCK_E1}, "k1"
        )


def test_two_password_resets_same_day_make_one(okta):
    day = utc_day(okta.clock.now())
    key = keys.send_password_reset(ALICE, day)
    okta.call("okta.send_password_reset", {"user": ALICE, "utc_date": day}, key)
    okta.call("okta.send_password_reset", {"user": ALICE, "utc_date": day}, key)
    assert read(okta)["resets_sent"] == [day.isoformat()]


def test_password_reset_next_day_makes_second(okta):
    day1 = utc_day(okta.clock.now())
    okta.call(
        "okta.send_password_reset",
        {"user": ALICE, "utc_date": day1},
        keys.send_password_reset(ALICE, day1),
    )
    okta.clock.advance(days=1)
    day2 = utc_day(okta.clock.now())
    okta.call(
        "okta.send_password_reset",
        {"user": ALICE, "utc_date": day2},
        keys.send_password_reset(ALICE, day2),
    )
    state = read(okta)
    assert len(state["resets_sent"]) == 2
    assert state["reset_sent_on"] == day2.isoformat()


def test_password_reset_rejects_datetime_and_bad_date(okta):
    with pytest.raises(InvalidArgument):
        okta.call("okta.send_password_reset", {"user": ALICE, "utc_date": T0}, "k1")
    with pytest.raises(InvalidArgument):
        okta.call("okta.send_password_reset", {"user": ALICE, "utc_date": "26/10/2026"}, "k2")
    assert read(okta)["resets_sent"] == []


def test_revoke_sessions_sets_sessions_to_zero(okta):
    okta.call(
        "okta.revoke_sessions",
        {"user": ALICE, "incident_id": "KAN-7"},
        keys.revoke_sessions(ALICE, "KAN-7"),
    )
    assert read(okta)["sessions_active"] == 0


def test_force_password_reset_bumps_password_epoch(okta):
    okta.call(
        "okta.force_password_reset",
        {"user": ALICE, "incident_id": "KAN-7"},
        keys.force_password_reset(ALICE, "KAN-7"),
    )
    assert read(okta)["password_epoch"] == 1
    okta.call(
        "okta.force_password_reset",
        {"user": ALICE, "incident_id": "KAN-8"},
        keys.force_password_reset(ALICE, "KAN-8"),
    )
    assert read(okta)["password_epoch"] == 2


def test_disable_mfa_clears_factors_without_approval_check(okta):
    okta.call(
        "okta.disable_mfa",
        {"user": ALICE, "approval_id": "APR-1"},
        keys.disable_mfa("APR-1"),
    )
    assert read(okta)["mfa_factors"] == []
    assert read(okta, BOB)["mfa_factors"] == ["push"]


def test_reset_restores_seed(okta):
    okta.call(
        "okta.revoke_sessions",
        {"user": ALICE, "incident_id": "KAN-7"},
        keys.revoke_sessions(ALICE, "KAN-7"),
    )
    okta.reset()
    assert read(okta)["sessions_active"] == 3


def test_missing_user_is_rejected_and_changes_nothing(okta):
    before = okta.snapshot()["state"]
    with pytest.raises(KeyError):
        okta.call(
            "okta.unlock_account",
            {"lock_epoch": LOCK_E1},
            keys.unlock_account(ALICE, LOCK_E1),
        )
    assert okta.snapshot()["state"] == before
    assert read(okta)["locked"] is True


def test_non_string_user_is_rejected_and_changes_nothing(okta):
    before = okta.snapshot()["state"]
    with pytest.raises(AttributeError):
        okta.call(
            "okta.unlock_account",
            {"user": 12345, "lock_epoch": LOCK_E1},
            keys.unlock_account(ALICE, LOCK_E1),
        )
    assert okta.snapshot()["state"] == before
    assert read(okta)["locked"] is True
