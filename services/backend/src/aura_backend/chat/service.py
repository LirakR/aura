"""Chat thread and message persistence backed by SurrealDB."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from aura_backend.chat.models import (
    ChatMessage,
    ChatThread,
    MessageRole,
    PaginatedMessages,
)
from aura_backend.db.connection import get_db
from aura_backend.websocket.manager import manager
from aura_backend.websocket.schemas import WSMessage

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s)


def _record_to_str(val) -> str:
    """Convert a SurrealDB RecordID or any value to a plain string."""
    return str(val)


# ── Threads ─────────────────────────────────────────────────────────


async def create_thread(project: str, title: str = "") -> ChatThread:
    db = get_db()
    tid = str(uuid.uuid4()).replace("-", "")
    now = _now()

    if not title:
        title = f"Chat {now[:10]}"

    result = await db.query(
        """
        CREATE chat_thread SET
            id = type::thing('chat_thread', $tid),
            project = $project,
            title = $title,
            created_at = $now,
            updated_at = $now
        """,
        {"tid": tid, "project": project, "title": title, "now": now},
    )

    # Fetch back the created record
    rows = await db.query(
        "SELECT * FROM chat_thread WHERE id = type::thing('chat_thread', $tid)",
        {"tid": tid},
    )
    row = rows[0] if rows else {}
    return ChatThread(
        id=_record_to_str(row.get("id", tid)),
        project=row.get("project", project),
        title=row.get("title", title),
        created_at=row.get("created_at", now),
        updated_at=row.get("updated_at", now),
    )


async def list_threads(project: str | None = None) -> list[ChatThread]:
    db = get_db()
    if project:
        rows = await db.query(
            "SELECT * FROM chat_thread WHERE project = $project ORDER BY updated_at DESC",
            {"project": project},
        )
    else:
        rows = await db.query(
            "SELECT * FROM chat_thread ORDER BY updated_at DESC"
        )

    return [
        ChatThread(
            id=_record_to_str(r["id"]),
            project=r["project"],
            title=r["title"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


async def get_thread(thread_id: str) -> ChatThread | None:
    db = get_db()
    rows = await db.query(
        "SELECT * FROM chat_thread WHERE id = type::thing('chat_thread', $tid)",
        {"tid": thread_id},
    )
    if not rows:
        return None
    r = rows[0]
    return ChatThread(
        id=_record_to_str(r["id"]),
        project=r["project"],
        title=r["title"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


async def delete_thread(thread_id: str) -> bool:
    db = get_db()
    # Delete messages first
    await db.query(
        "DELETE chat_message WHERE thread = type::thing('chat_thread', $tid)",
        {"tid": thread_id},
    )
    await db.query(
        "DELETE type::thing('chat_thread', $tid)",
        {"tid": thread_id},
    )
    return True


# ── Messages ────────────────────────────────────────────────────────


async def add_message(
    thread_id: str,
    role: MessageRole,
    content: str,
    metadata: dict | None = None,
) -> ChatMessage:
    db = get_db()
    mid = str(uuid.uuid4()).replace("-", "")
    now = _now()

    await db.query(
        """
        CREATE chat_message SET
            id = type::thing('chat_message', $mid),
            thread = type::thing('chat_thread', $tid),
            role = $role,
            content = $content,
            metadata = $metadata,
            created_at = $now
        """,
        {
            "mid": mid,
            "tid": thread_id,
            "role": str(role),
            "content": content,
            "metadata": metadata or {},
            "now": now,
        },
    )

    # Update thread's updated_at
    await db.query(
        "UPDATE type::thing('chat_thread', $tid) SET updated_at = $now",
        {"tid": thread_id, "now": now},
    )

    msg = ChatMessage(
        id=f"chat_message:{mid}",
        thread=f"chat_thread:{thread_id}",
        role=role,
        content=content,
        metadata=metadata,
        created_at=now,
    )

    # Broadcast to WS clients
    await manager.broadcast(
        WSMessage(
            type="chat.message.new",
            payload={
                "thread_id": thread_id,
                "message": msg.model_dump(),
            },
        )
    )

    return msg


async def get_messages(
    thread_id: str,
    cursor: str | None = None,
    limit: int = 50,
) -> PaginatedMessages:
    db = get_db()

    if cursor:
        rows = await db.query(
            """
            SELECT * FROM chat_message
            WHERE thread = type::thing('chat_thread', $tid)
              AND created_at < $cursor
            ORDER BY created_at DESC
            LIMIT $limit
            """,
            {"tid": thread_id, "cursor": cursor, "limit": limit + 1},
        )
    else:
        rows = await db.query(
            """
            SELECT * FROM chat_message
            WHERE thread = type::thing('chat_thread', $tid)
            ORDER BY created_at DESC
            LIMIT $limit
            """,
            {"tid": thread_id, "limit": limit + 1},
        )

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    messages = [
        ChatMessage(
            id=_record_to_str(r["id"]),
            thread=_record_to_str(r["thread"]),
            role=r["role"],
            content=r["content"],
            metadata=r.get("metadata"),
            created_at=r["created_at"],
        )
        for r in rows
    ]

    # Return in chronological order
    messages.reverse()

    next_cursor = messages[0].created_at if messages and has_more else None

    return PaginatedMessages(
        messages=messages,
        cursor=next_cursor,
        has_more=has_more,
    )


# ── Convenience helpers ─────────────────────────────────────────────


async def add_system_message(thread_id: str, content: str, metadata: dict | None = None) -> ChatMessage:
    """Add a system message to a thread (e.g., file change notifications)."""
    return await add_message(thread_id, MessageRole.system, content, metadata=metadata)


async def get_active_thread_for_project(project: str) -> ChatThread | None:
    """Get the most recently updated thread for a project."""
    db = get_db()
    rows = await db.query(
        "SELECT * FROM chat_thread WHERE project = $project ORDER BY updated_at DESC LIMIT 1",
        {"project": project},
    )
    if not rows:
        return None
    r = rows[0]
    return ChatThread(
        id=_record_to_str(r["id"]),
        project=r["project"],
        title=r["title"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )
