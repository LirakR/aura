"""Pydantic models for chat threads and messages."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ── Request models ──────────────────────────────────────────────────

class ChatThreadCreate(BaseModel):
    project: str
    title: str = ""


class ChatMessageCreate(BaseModel):
    role: MessageRole = MessageRole.user
    content: str


# ── Response models ─────────────────────────────────────────────────

class ChatThread(BaseModel):
    id: str
    project: str
    title: str
    created_at: str
    updated_at: str


class ChatMessage(BaseModel):
    id: str
    thread: str
    role: MessageRole
    content: str
    metadata: dict | None = None
    created_at: str


class PaginatedMessages(BaseModel):
    messages: list[ChatMessage]
    cursor: str | None = None
    has_more: bool = False
