"""Agent provider protocol and shared dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator, Protocol, runtime_checkable


@dataclass
class SessionInfo:
    thread_id: str
    provider: str
    model: str


@dataclass
class TurnInfo:
    thread_id: str
    request_id: str


@dataclass
class ProviderEvent:
    """Structured event emitted by agent adapters.

    kind values:
      turn.started       — Turn began
      turn.completed     — Turn done (full_text = final assistant message)
      item.started       — A new item (message, command, file_change, reasoning)
      item.completed     — Item finished
      message.delta      — Text delta for current agent message
      approval.request   — Needs user approval
      error              — Something went wrong
    """

    kind: str
    thread_id: str
    # Text streaming
    text_delta: str | None = None
    full_text: str | None = None
    # Item tracking
    item_id: str | None = None
    item_type: str | None = None  # "message", "command", "file_change", "reasoning"
    item_data: dict | None = None  # command, cwd, output, files, etc.
    # Approval
    request_id: str | None = None
    approval_data: dict | None = None
    # Error
    error: str | None = None


@runtime_checkable
class AgentProvider(Protocol):
    async def start_session(
        self, thread_id: str, cwd: str, model: str
    ) -> SessionInfo: ...

    async def send_turn(
        self, thread_id: str, message: str, context: str | None = None
    ) -> TurnInfo: ...

    async def interrupt_turn(self, thread_id: str) -> None: ...

    async def respond_to_approval(
        self, thread_id: str, request_id: str, decision: str
    ) -> None: ...

    async def stop_session(self, thread_id: str) -> None: ...

    async def stream_events(self, thread_id: str) -> AsyncIterator[ProviderEvent]: ...
