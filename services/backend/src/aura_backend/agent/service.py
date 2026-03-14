"""Agent provider service — singleton managing active sessions."""

from __future__ import annotations

import asyncio
import logging

from aura_backend.agent.base import ProviderEvent
from aura_backend.agent.codex.adapter import CodexAdapter
from aura_backend.chat.models import MessageRole
from aura_backend.config import settings
from aura_backend.websocket.manager import manager
from aura_backend.websocket.schemas import WSMessage

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(self) -> None:
        self._adapters: dict[str, CodexAdapter] = {}
        self._event_tasks: dict[str, asyncio.Task] = {}

    async def send_message(
        self,
        thread_id: str,
        content: str,
        project_path: str | None = None,
        project_name: str | None = None,
        context: str | None = None,
    ) -> None:
        """Start an agent turn for the given thread."""
        adapter = self._adapters.get(thread_id)

        if adapter is None:
            cwd = project_path or "."
            adapter = CodexAdapter(
                thread_id=thread_id,
                cwd=cwd,
                model=settings.agent_codex_model,
            )
            await adapter.start()
            self._adapters[thread_id] = adapter

        # Build context from KB if not already provided
        if context is None and project_name:
            try:
                from aura_backend.agent.context import build_turn_context

                context = await build_turn_context(project_name, content)
            except Exception:
                logger.warning("Failed to build turn context", exc_info=True)

        turn_info = await adapter.send_turn(content, context=context)

        # Start event consumer
        task = asyncio.create_task(self._consume_events(thread_id))
        # Cancel any existing event task for this thread
        old_task = self._event_tasks.get(thread_id)
        if old_task and not old_task.done():
            old_task.cancel()
        self._event_tasks[thread_id] = task

    async def interrupt(self, thread_id: str) -> None:
        adapter = self._adapters.get(thread_id)
        if adapter:
            await adapter.interrupt()

    async def respond_to_approval(
        self, thread_id: str, request_id: str, decision: str
    ) -> None:
        adapter = self._adapters.get(thread_id)
        if adapter:
            await adapter.respond_to_approval(request_id, decision)

    async def stop_session(self, thread_id: str) -> None:
        task = self._event_tasks.pop(thread_id, None)
        if task and not task.done():
            task.cancel()

        adapter = self._adapters.pop(thread_id, None)
        if adapter:
            await adapter.stop()

    async def shutdown(self) -> None:
        """Stop all sessions — called at app shutdown."""
        thread_ids = list(self._adapters.keys())
        for tid in thread_ids:
            await self.stop_session(tid)

    async def _consume_events(self, thread_id: str) -> None:
        """Read events from the adapter and broadcast via WebSocket."""
        adapter = self._adapters.get(thread_id)
        if not adapter:
            return

        try:
            async for event in adapter.stream_events():
                await self._broadcast_event(event)

                if event.kind == "turn.completed" and event.full_text:
                    # Persist the assistant message
                    from aura_backend.chat.service import add_message

                    await add_message(
                        thread_id=thread_id,
                        role=MessageRole.assistant,
                        content=event.full_text,
                    )
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.error("Event consumer error for thread %s", thread_id, exc_info=True)

    async def _broadcast_event(self, event: ProviderEvent) -> None:
        """Map a ProviderEvent to a WSMessage and broadcast."""
        payload: dict = {"thread_id": event.thread_id}

        if event.kind == "message.delta":
            payload["delta"] = event.text_delta
            payload["item_id"] = event.item_id
            msg_type = "agent.message.delta"
        elif event.kind == "item.started":
            payload["item_id"] = event.item_id
            payload["item_type"] = event.item_type
            msg_type = "agent.item.started"
        elif event.kind == "item.completed":
            payload["item_id"] = event.item_id
            payload["item_type"] = event.item_type
            payload["text"] = event.full_text
            payload["data"] = event.item_data
            msg_type = "agent.item.completed"
        elif event.kind == "item.output":
            payload["item_id"] = event.item_id
            payload["item_type"] = event.item_type
            payload["delta"] = event.text_delta
            msg_type = "agent.item.output"
        elif event.kind == "turn.started":
            msg_type = "agent.turn.started"
        elif event.kind == "turn.completed":
            payload["full_text"] = event.full_text
            msg_type = "agent.turn.completed"
        elif event.kind == "approval.request":
            payload["request_id"] = event.request_id
            payload["data"] = event.approval_data
            msg_type = "agent.approval.request"
        elif event.kind == "error":
            payload["error"] = event.error
            msg_type = "agent.error"
        else:
            return

        await manager.broadcast(WSMessage(type=msg_type, payload=payload))


# Singleton
_service: ProviderService | None = None


def get_provider_service() -> ProviderService:
    global _service
    if _service is None:
        _service = ProviderService()
    return _service


async def shutdown_provider_service() -> None:
    global _service
    if _service:
        await _service.shutdown()
        _service = None
