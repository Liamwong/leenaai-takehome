"""Each CTX §4 recipe: deterministic, and the key changes when (and only
when) one of its stated components changes."""

from datetime import date, datetime, timedelta, timezone

import pytest

from helix_agent import keys
from helix_agent.clock import FixedClock, utc_day

LOCK = datetime(2026, 10, 25, 9, 30, tzinfo=timezone.utc)
DAY = date(2026, 10, 25)

# recipe -> (base kwargs, {component: changed value})
RECIPES = {
    keys.unlock_account: (
        {"account": "alice@helix.example", "lock_epoch": LOCK},
        {"account": "bob@helix.example", "lock_epoch": LOCK + timedelta(minutes=20)},
    ),
    keys.send_password_reset: (
        {"user": "alice@helix.example", "day": DAY},
        {"user": "bob@helix.example", "day": DAY + timedelta(days=1)},
    ),
    keys.create_request: (
        {"user": "alice@helix.example", "item": "usb_exception", "day": DAY},
        {"user": "bob@helix.example", "item": "travel_exception", "day": DAY + timedelta(days=1)},
    ),
    keys.grant_admin: (
        {"user": "alice@helix.example", "session_id": "KAN-12"},
        {"user": "bob@helix.example", "session_id": "KAN-13"},
    ),
    keys.create_case: (
        {"asset_id": "LT-0042", "case_type": "lost_stolen"},
        {"asset_id": "LT-0043", "case_type": "offboarding"},
    ),
    keys.create_approval: (
        {
            "requester": "alice@helix.example",
            "target": "alice@helix.example",
            "action": "iam.grant_access",
            "params": {"system": "finance-db", "role": "read"},
        },
        {
            "requester": "bob@helix.example",
            "target": "carol@helix.example",
            "action": "okta.disable_mfa",
            "params": {"system": "finance-db", "role": "write"},
        },
    ),
    keys.grant_access: ({"approval_id": "APR-1"}, {"approval_id": "APR-2"}),
    keys.disable_mfa: ({"approval_id": "APR-1"}, {"approval_id": "APR-2"}),
    keys.revoke_sessions: (
        {"user": "alice@helix.example", "incident_id": "KAN-7"},
        {"user": "bob@helix.example", "incident_id": "KAN-8"},
    ),
    keys.force_password_reset: (
        {"user": "alice@helix.example", "incident_id": "KAN-7"},
        {"user": "bob@helix.example", "incident_id": "KAN-8"},
    ),
    keys.open_incident: ({"ticket_id": "KAN-7"}, {"ticket_id": "KAN-8"}),
    keys.page_oncall: ({"ticket_id": "KAN-7"}, {"ticket_id": "KAN-8"}),
}

CASES = [
    pytest.param(recipe, base, component, value, id=f"{recipe.__name__}-{component}")
    for recipe, (base, changes) in RECIPES.items()
    for component, value in changes.items()
]


@pytest.mark.parametrize("recipe", list(RECIPES), ids=lambda r: r.__name__)
def test_recipe_is_deterministic(recipe):
    base, _ = RECIPES[recipe]
    assert recipe(**base) == recipe(**base)


@pytest.mark.parametrize("recipe, base, component, value", CASES)
def test_key_changes_when_component_changes(recipe, base, component, value):
    assert recipe(**{**base, component: value}) != recipe(**base)


def test_user_ids_are_case_insensitive():
    assert keys.send_password_reset("Alice@Helix.example ", DAY) == keys.send_password_reset(
        "alice@helix.example", DAY
    )


def test_unlock_ignores_everything_but_account_and_epoch():
    # Same lockout seen at a different wall-clock time is the same action.
    as_int = int(LOCK.timestamp())
    other_tz = LOCK.astimezone(timezone(timedelta(hours=-4)))
    assert keys.unlock_account("alice@helix.example", LOCK) == keys.unlock_account(
        "alice@helix.example", as_int
    ) == keys.unlock_account("alice@helix.example", other_tz)


def test_request_hash_ignores_param_order_but_not_values():
    a = keys.create_approval("a@x", "a@x", "iam.grant_access", {"system": "s", "role": "r"})
    b = keys.create_approval("a@x", "a@x", "iam.grant_access", {"role": "r", "system": "s"})
    c = keys.create_approval("a@x", "a@x", "iam.grant_access", {"role": "r", "system": "s2"})
    assert a == b != c
    assert len(a) == 64


def test_shared_recipes_produce_same_key_but_store_scopes_by_tool():
    # Documented: the store keys on (tool, key), so these do not collide.
    assert keys.revoke_sessions("a@x", "KAN-7") == keys.force_password_reset("a@x", "KAN-7")


@pytest.mark.parametrize(
    "call",
    [
        lambda: keys.grant_access(""),
        lambda: keys.open_incident("   "),
        lambda: keys.create_case("LT|1", "lost_stolen"),
        lambda: keys.unlock_account("a@x", datetime(2026, 10, 25, 9, 30)),
    ],
    ids=["empty", "blank", "separator", "naive-datetime"],
)
def test_invalid_components_rejected(call):
    with pytest.raises(ValueError):
        call()


@pytest.mark.parametrize(
    "call",
    [
        lambda: keys.send_password_reset("a@x", LOCK),
        lambda: keys.unlock_account("a@x", "1729848600"),
        lambda: keys.unlock_account("a@x", True),
    ],
    ids=["datetime-as-day", "str-epoch", "bool-epoch"],
)
def test_wrong_types_rejected(call):
    with pytest.raises(TypeError):
        call()


def test_utc_day_crosses_local_midnight():
    # 21:30 in New York on Oct 25 is already Oct 26 in UTC.
    ny = timezone(timedelta(hours=-4))
    assert utc_day(datetime(2026, 10, 25, 21, 30, tzinfo=ny)) == date(2026, 10, 26)


def test_fixed_clock_is_deterministic_and_rejects_naive():
    clock = FixedClock(LOCK)
    assert clock.now() == LOCK
    clock.advance(days=1)
    assert utc_day(clock.now()) == DAY + timedelta(days=1)
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 1, 1))
