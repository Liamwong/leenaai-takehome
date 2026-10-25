from datetime import datetime, timezone

import pytest

from helix_agent.clock import FixedClock
from helix_agent.mocks import MissingIdempotencyKey, MockService, ReplayConflict, UnknownTool

T0 = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


class ToyService(MockService):
    """Counts state changes so tests can prove exactly-once execution."""

    def __init__(self) -> None:
        super().__init__(clock=FixedClock(T0))
        self.register("toy.bump", self._bump, mutating=True)
        self.register("toy.other_bump", self._bump, mutating=True)
        self.register("toy.read", self._read, mutating=False)
        self.register("toy.half_then_fail", self._half_then_fail, mutating=True)

    def _bump(self, args):
        entity = self._get("counter", args["name"]) or {"n": 0}
        entity = {"n": entity["n"] + args.get("by", 1)}
        self._put("counter", args["name"], entity)
        return {"ok": True, "n": entity["n"]}

    def _read(self, args):
        return {"counter": self._get("counter", args["name"])}

    def _half_then_fail(self, args):
        self._put("counter", args["name"], {"n": 999})
        raise RuntimeError("second step failed")


@pytest.fixture
def svc():
    return ToyService()


def count(svc, name="a"):
    state = svc.read_state("counter", name)
    return state["n"] if state else 0


def test_repeat_key_same_args_returns_identical_result_and_one_state_change(svc):
    first = svc.call("toy.bump", {"name": "a"}, "k1")
    second = svc.call("toy.bump", {"name": "a"}, "k1")
    assert first == second == {"ok": True, "n": 1}
    assert count(svc) == 1


def test_arg_order_does_not_matter_for_replay(svc):
    svc.call("toy.bump", {"name": "a", "by": 2}, "k1")
    svc.call("toy.bump", {"by": 2, "name": "a"}, "k1")
    assert count(svc) == 2


def test_new_key_executes_again(svc):
    svc.call("toy.bump", {"name": "a"}, "k1")
    svc.call("toy.bump", {"name": "a"}, "k2")
    assert count(svc) == 2


def test_repeat_key_different_args_raises_and_does_not_execute(svc):
    svc.call("toy.bump", {"name": "a"}, "k1")
    with pytest.raises(ReplayConflict) as exc:
        svc.call("toy.bump", {"name": "a", "by": 5}, "k1")
    assert exc.value.tool == "toy.bump" and exc.value.idempotency_key == "k1"
    assert count(svc) == 1


def test_keys_are_scoped_per_tool(svc):
    svc.call("toy.bump", {"name": "a"}, "shared")
    svc.call("toy.other_bump", {"name": "a"}, "shared")
    assert count(svc) == 2


@pytest.mark.parametrize("key", [None, "", "   "])
def test_state_changing_call_requires_key(svc, key):
    with pytest.raises(MissingIdempotencyKey):
        svc.call("toy.bump", {"name": "a"}, key)
    assert count(svc) == 0


def test_read_only_call_needs_no_key(svc):
    svc.call("toy.bump", {"name": "a"}, "k1")
    assert svc.call("toy.read", {"name": "a"}) == {"counter": {"n": 1}}


def test_unknown_tool(svc):
    with pytest.raises(UnknownTool):
        svc.call("okta.nope", {}, "k1")


def test_duplicate_registration_rejected(svc):
    with pytest.raises(ValueError):
        svc.register("toy.bump", lambda a: {}, mutating=True)


def test_failed_handler_rolls_back_state_and_records_nothing(svc):
    svc.call("toy.bump", {"name": "a"}, "k1")
    with pytest.raises(RuntimeError):
        svc.call("toy.half_then_fail", {"name": "a"}, "k2")
    assert count(svc) == 1
    assert svc.replay_record("toy.half_then_fail", "k2") is None
    # A retry with the same key runs again rather than replaying a failure.
    with pytest.raises(RuntimeError):
        svc.call("toy.half_then_fail", {"name": "a"}, "k2")


def test_read_state_is_independent_of_write_response(svc):
    result = svc.call("toy.bump", {"name": "a"}, "k1")
    result["n"] = 42
    state = svc.read_state("counter", "a")
    state["n"] = 43
    assert svc.read_state("counter", "a") == {"n": 1}
    assert svc.call("toy.bump", {"name": "a"}, "k1") == {"ok": True, "n": 1}


def test_read_state_missing_entity_is_none(svc):
    assert svc.read_state("counter", "nobody") is None
    assert svc.read_state("no_such_entity", "x") is None


def test_replay_record_and_snapshot(svc):
    svc.call("toy.bump", {"name": "a"}, "k1")
    record = svc.replay_record("toy.bump", "k1")
    assert record is not None and record.created_at == T0
    snap = svc.snapshot()
    assert snap["state"] == {"counter": {"a": {"n": 1}}}
    assert snap["idempotency"][0]["idempotency_key"] == "k1"
    assert snap["idempotency"][0]["created_at"] == T0.isoformat()


def test_reset_restores_empty_state(svc):
    svc.call("toy.bump", {"name": "a"}, "k1")
    svc.reset()
    assert svc.snapshot() == {"state": {}, "idempotency": []}
    assert svc.read_state("counter", "a") is None
    # After reset the key is fresh, so the call executes.
    svc.call("toy.bump", {"name": "a"}, "k1")
    assert count(svc) == 1
