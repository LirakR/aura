"""Chat REST API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from aura_backend.chat.models import (
    ChatMessageCreate,
    ChatThread,
    ChatThreadCreate,
    PaginatedMessages,
)
from aura_backend.chat.service import (
    add_message,
    create_thread,
    delete_thread,
    get_messages,
    get_thread,
    list_threads,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/threads", response_model=ChatThread)
async def create_thread_endpoint(body: ChatThreadCreate) -> ChatThread:
    return await create_thread(project=body.project, title=body.title)


@router.get("/threads", response_model=list[ChatThread])
async def list_threads_endpoint(
    project: str | None = Query(default=None),
) -> list[ChatThread]:
    return await list_threads(project=project)


@router.get("/threads/{thread_id}", response_model=ChatThread)
async def get_thread_endpoint(thread_id: str) -> ChatThread:
    thread = await get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.delete("/threads/{thread_id}")
async def delete_thread_endpoint(thread_id: str) -> dict:
    await delete_thread(thread_id)
    return {"status": "deleted"}


@router.post("/threads/{thread_id}/messages")
async def add_message_endpoint(
    thread_id: str,
    body: ChatMessageCreate,
) -> dict:
    thread = await get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    msg = await add_message(
        thread_id=thread_id,
        role=body.role,
        content=body.content,
    )
    return msg.model_dump()


@router.get("/threads/{thread_id}/messages", response_model=PaginatedMessages)
async def get_messages_endpoint(
    thread_id: str,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> PaginatedMessages:
    thread = await get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    return await get_messages(thread_id=thread_id, cursor=cursor, limit=limit)
