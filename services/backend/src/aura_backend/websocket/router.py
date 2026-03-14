import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from aura_backend.websocket.manager import manager
from aura_backend.websocket.schemas import WSMessage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    client_id = await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "heartbeat.ping":
                pong = WSMessage(type="heartbeat.pong")
                await manager.send_to(client_id, pong)

            elif msg_type == "engine.status":
                msg = WSMessage(
                    type="engine.status",
                    payload=data.get("payload", {}),
                )
                await manager.broadcast_engine_status(msg, sender_id=client_id)

            elif msg_type == "project.scan":
                await _handle_project_scan(client_id, data)

            elif msg_type == "project.file_changed":
                await _handle_file_changed(client_id, data)

            elif msg_type == "project.file_deleted":
                await _handle_file_deleted(client_id, data)

            elif msg_type == "chat.send":
                await _handle_chat_send(client_id, data)

            elif msg_type == "agent.interrupt":
                await _handle_agent_interrupt(client_id, data)

            elif msg_type == "agent.approval.respond":
                await _handle_agent_approval(client_id, data)

    except WebSocketDisconnect:
        was_engine = manager.is_engine(client_id)
        manager.disconnect(client_id)
        if was_engine:
            msg = WSMessage(type="engine.disconnect")
            await manager.broadcast(msg)


async def _handle_project_scan(client_id: str, data: dict) -> None:
    """Handle full project scan from AuraBridge."""
    from aura_backend.kb.project_store import store_project_scan

    payload = data.get("payload", {})
    try:
        result = await store_project_scan(
            project_name=payload.get("project_name", "default"),
            engine=payload.get("engine", "godot"),
            version=payload.get("engine_version"),
            project_path=payload.get("project_path"),
            files=payload.get("files", []),
        )
        ack = WSMessage(type="project.scan.ack", payload=result)
    except Exception:
        logger.error("project.scan failed", exc_info=True)
        ack = WSMessage(
            type="project.scan.ack",
            payload={"error": "scan failed"},
        )

    await manager.send_to(client_id, ack)


async def _handle_file_changed(client_id: str, data: dict) -> None:
    """Handle single file update from file watcher."""
    from aura_backend.kb.project_store import store_project_file

    payload = data.get("payload", {})
    try:
        result = await store_project_file(
            project_name=payload.get("project_name", "default"),
            file_path=payload["path"],
            content=payload["content"],
            language=payload.get("language"),
        )
        ack = WSMessage(type="project.file_changed.ack", payload=result)
    except Exception:
        logger.error("project.file_changed failed", exc_info=True)
        ack = WSMessage(
            type="project.file_changed.ack",
            payload={"error": "store failed"},
        )

    await manager.send_to(client_id, ack)

    # Broadcast file change to all clients
    await manager.broadcast(
        WSMessage(
            type="project.file_changed",
            payload=payload,
        ),
        exclude=client_id,
    )

    # Create system message in active chat thread
    try:
        from aura_backend.chat.service import (
            add_system_message,
            get_active_thread_for_project,
        )

        project_name = payload.get("project_name", "default")
        file_path = payload.get("path", "")
        thread = await get_active_thread_for_project(project_name)
        if thread:
            tid = thread.id.split(":")[1] if ":" in thread.id else thread.id
            await add_system_message(
                tid,
                f"File changed: {file_path}",
                metadata={"type": "file_change", "path": file_path},
            )
    except Exception:
        logger.debug("Failed to create file change system message", exc_info=True)


async def _handle_file_deleted(client_id: str, data: dict) -> None:
    """Handle file removal."""
    from aura_backend.kb.project_store import delete_project_file

    payload = data.get("payload", {})
    try:
        await delete_project_file(
            project_name=payload.get("project_name", "default"),
            file_path=payload["path"],
        )
        ack = WSMessage(type="project.file_deleted.ack", payload={"status": "deleted"})
    except Exception:
        logger.error("project.file_deleted failed", exc_info=True)
        ack = WSMessage(
            type="project.file_deleted.ack",
            payload={"error": "delete failed"},
        )

    await manager.send_to(client_id, ack)

    # Broadcast file deletion to all clients
    await manager.broadcast(
        WSMessage(type="project.file_deleted", payload=payload),
        exclude=client_id,
    )


async def _handle_chat_send(client_id: str, data: dict) -> None:
    """Handle chat message that triggers an agent turn."""
    from aura_backend.agent.service import get_provider_service
    from aura_backend.chat.models import MessageRole
    from aura_backend.chat.service import add_message, get_thread

    payload = data.get("payload", {})
    thread_id = payload.get("thread_id", "")
    content = payload.get("content", "")

    if not thread_id or not content:
        return

    # Persist the user message
    await add_message(thread_id=thread_id, role=MessageRole.user, content=content)

    # Look up project path for the thread
    thread = await get_thread(thread_id)
    project_path = None
    if thread:
        from aura_backend.db.connection import get_db

        db = get_db()
        rows = await db.query(
            "SELECT path FROM kb_project WHERE name = $name",
            {"name": thread.project},
        )
        if rows:
            project_path = rows[0].get("path")

    # Start agent turn
    try:
        service = get_provider_service()
        await service.send_message(
            thread_id=thread_id,
            content=content,
            project_path=project_path,
            project_name=thread.project if thread else None,
        )
    except Exception:
        logger.error("Agent turn failed for thread %s", thread_id, exc_info=True)
        await manager.broadcast(
            WSMessage(
                type="agent.error",
                payload={"thread_id": thread_id, "error": "Agent turn failed"},
            )
        )


async def _handle_agent_interrupt(client_id: str, data: dict) -> None:
    """Handle agent turn interruption."""
    from aura_backend.agent.service import get_provider_service

    payload = data.get("payload", {})
    thread_id = payload.get("thread_id", "")
    if thread_id:
        service = get_provider_service()
        await service.interrupt(thread_id)


async def _handle_agent_approval(client_id: str, data: dict) -> None:
    """Handle approval response from the client."""
    from aura_backend.agent.service import get_provider_service

    payload = data.get("payload", {})
    thread_id = payload.get("thread_id", "")
    request_id = payload.get("request_id", "")
    decision = payload.get("decision", "deny")
    if thread_id and request_id:
        service = get_provider_service()
        await service.respond_to_approval(thread_id, request_id, decision)
