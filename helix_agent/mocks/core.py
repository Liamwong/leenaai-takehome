"""Shared base for every mock tool: idempotency store and state read-back.

Concrete tools (directory, Okta, ServiceNow, IAM, SOC, ...) subclass
MockService and register one handler per tool. The base class guarantees:

- A state-changing call must carry an idempotency key.
- A repeat key with identical args returns the stored result and changes
  nothing. A repeat key with different args raises ReplayConflict and does
  not execute.
- A handler that raises leaves state exactly as it was, and nothing is
  recorded, so a retry can run it again. Because of this, a half-finished
  action (the step-2-fails failure mode) must be built as two separate
  calls: the first succeeds and keeps its result, the second fails. A single
  handler that writes and then raises would be undone, hiding the partial
  state the agent is meant to detect and roll back or flag.
- A read-only tool that changes state raises ReadOnlyViolation, and the
  change is undone.
- read_state() reads the stored entity, independent of any write response,
  so callers can verify an effect instead of trusting the reply.

Keys are scoped per tool. Key recipes live in helix_agent.keys.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

from helix_agent.clock import Clock, SystemClock
from helix_agent.keys import canonical_json

Handler = Callable[[dict[str, Any]], dict[str, Any]]


class MockError(Exception):
    """Base class for errors raised by the mock layer itself."""


class UnknownTool(MockError):
    def __init__(self, tool: str) -> None:
        super().__init__(f"unknown tool: {tool}")
        self.tool = tool


class MissingIdempotencyKey(MockError):
    def __init__(self, tool: str) -> None:
        super().__init__(f"{tool} changes state and requires an idempotency key")
        self.tool = tool


class ReadOnlyViolation(MockError):
    """A tool registered as read-only changed state."""

    def __init__(self, tool: str) -> None:
        super().__init__(f"{tool} is registered read-only but changed state")
        self.tool = tool


class ReplayConflict(MockError):
    """The key was already used for this tool with different arguments."""

    def __init__(self, tool: str, idempotency_key: str) -> None:
        super().__init__(f"{tool}: idempotency key {idempotency_key!r} reused with different args")
        self.tool = tool
        self.idempotency_key = idempotency_key


@dataclass(frozen=True)
class IdempotencyRecord:
    tool: str
    idempotency_key: str
    args_hash: str
    result: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class _ToolSpec:
    handler: Handler
    mutating: bool


class MockService:
    def __init__(self, clock: Clock | None = None) -> None:
        self.clock: Clock = clock or SystemClock()
        self._tools: dict[str, _ToolSpec] = {}
        self._state: dict[str, dict[str, dict[str, Any]]] = {}
        self._records: dict[tuple[str, str], IdempotencyRecord] = {}

    # -- registration -------------------------------------------------------

    def register(self, tool: str, handler: Handler, *, mutating: bool) -> None:
        if tool in self._tools:
            raise ValueError(f"tool already registered: {tool}")
        self._tools[tool] = _ToolSpec(handler, mutating)

    @property
    def tools(self) -> frozenset[str]:
        return frozenset(self._tools)

    # -- calls --------------------------------------------------------------

    def call(
        self, tool: str, args: Mapping[str, Any], idempotency_key: str | None = None
    ) -> dict[str, Any]:
        spec = self._tools.get(tool)
        if spec is None:
            raise UnknownTool(tool)
        args = copy.deepcopy(dict(args))

        if not spec.mutating:
            # A read-only tool that writes would skip the idempotency store,
            # so undo the write and fail loudly.
            before = copy.deepcopy(self._state)
            result = spec.handler(args)
            if self._state != before:
                self._state = before
                raise ReadOnlyViolation(tool)
            return copy.deepcopy(result)

        if not idempotency_key or not idempotency_key.strip():
            raise MissingIdempotencyKey(tool)
        args_hash = hashlib.sha256(canonical_json(args).encode()).hexdigest()

        prior = self._records.get((tool, idempotency_key))
        if prior is not None:
            if prior.args_hash != args_hash:
                raise ReplayConflict(tool, idempotency_key)
            return copy.deepcopy(prior.result)

        before = copy.deepcopy(self._state)
        try:
            result = spec.handler(args)
        except BaseException:
            self._state = before
            raise
        self._records[(tool, idempotency_key)] = IdempotencyRecord(
            tool=tool,
            idempotency_key=idempotency_key,
            args_hash=args_hash,
            result=copy.deepcopy(result),
            created_at=self.clock.now(),
        )
        return copy.deepcopy(result)

    def replay_record(self, tool: str, idempotency_key: str) -> IdempotencyRecord | None:
        """The stored record for a key, if that call already executed."""
        return self._records.get((tool, idempotency_key))

    # -- state --------------------------------------------------------------

    def read_state(self, entity: str, entity_id: str) -> dict[str, Any] | None:
        stored = self._state.get(entity, {}).get(entity_id)
        return copy.deepcopy(stored)

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": copy.deepcopy(self._state),
            "idempotency": [
                {**asdict(r), "created_at": r.created_at.isoformat()}
                for r in self._records.values()
            ],
        }

    def reset(self) -> None:
        self._state = {}
        self._records = {}

    # -- for handlers -------------------------------------------------------

    def _get(self, entity: str, entity_id: str) -> dict[str, Any] | None:
        return self._state.get(entity, {}).get(entity_id)

    def _put(self, entity: str, entity_id: str, value: dict[str, Any]) -> None:
        self._state.setdefault(entity, {})[entity_id] = value
