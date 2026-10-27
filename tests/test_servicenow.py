from datetime import UTC, datetime

import pytest

from helix_agent import keys
from helix_agent.clock import FixedClock, utc_day
from helix_agent.mocks import InvalidArgument, ServiceNowMock
from helix_agent.mocks.servicenow import REQUEST_STATES

T0 = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
ALICE = "alice@helix.example"


@pytest.fixture
def snow():
    return ServiceNowMock(clock=FixedClock(T0))


def create(snow, item="USB Exception", fields=None, key=None):
    fields = {"requester": ALICE, **(fields or {})}
    key = key or keys.create_request(ALICE, item, utc_day(snow.clock.now()))
    return snow.call("servicenow.create_request", {"item": item, "fields": fields}, key)


def test_tool_names_match_catalog(snow):
    assert snow.tools == frozenset({"servicenow.create_request"})


def test_request_is_stored_submitted_even_if_fields_claim_granted(snow):
    result = create(snow, fields={"state": "GRANTED"})
    assert result["state"] == "SUBMITTED"
    assert snow.read_state("request", result["id"])["state"] == "SUBMITTED"


def test_only_submitted_is_a_request_state():
    assert frozenset({"SUBMITTED"}) == REQUEST_STATES


def test_mixed_case_requester_is_stored_lower_case(snow):
    result = create(snow, fields={"requester": "Alice@Helix.Example"})
    stored = snow.read_state("request", result["id"])
    assert stored["requester"] == ALICE
    assert stored["fields"]["requester"] == ALICE


def test_mixed_case_requester_retry_with_same_key_returns_same_request(snow):
    key = keys.create_request(ALICE, "USB Exception", utc_day(snow.clock.now()))
    first = create(snow, key=key)
    second = create(snow, fields={"requester": "Alice@Helix.Example"}, key=key)
    assert first == second
    assert len(snow.snapshot()["state"]["request"]) == 1


def test_same_requester_item_day_and_key_returns_same_id(snow):
    first = create(snow)
    second = create(snow)
    assert first["id"] == second["id"]
    assert len(snow.snapshot()["state"]["request"]) == 1


def test_new_day_files_a_new_request(snow):
    first = create(snow)
    snow.clock.advance(days=1)
    second = create(snow)
    assert first["id"] != second["id"]
    assert len(snow.snapshot()["state"]["request"]) == 2


@pytest.mark.parametrize(
    "item", ["Travel Exception", "USB Exception", "Software", "Peripheral Catalog"]
)
def test_catalog_items_are_accepted(snow, item):
    assert create(snow, item=item)["item"] == item


def test_unknown_item_raises_and_stores_nothing(snow):
    with pytest.raises(InvalidArgument):
        create(snow, item="Pony Exception")
    assert snow.snapshot()["state"] == {}
    assert snow.replay_record("servicenow.create_request", "anything") is None


def test_missing_requester_raises_and_stores_nothing(snow):
    with pytest.raises(InvalidArgument):
        snow.call(
            "servicenow.create_request",
            {"item": "Software", "fields": {}},
            "k1",
        )
    assert snow.snapshot()["state"] == {}


@pytest.mark.parametrize("requester", [None, 12345, ["alice@helix.example"]])
def test_non_string_requester_is_rejected_and_stores_nothing(snow, requester):
    with pytest.raises(InvalidArgument):
        snow.call(
            "servicenow.create_request",
            {"item": "Software", "fields": {"requester": requester}},
            "k1",
        )
    assert snow.snapshot()["state"] == {}
    assert snow.replay_record("servicenow.create_request", "k1") is None
