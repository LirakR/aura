"""File operations for the agent — read/write/list through KB store."""

from __future__ import annotations

import logging

from aura_backend.db.connection import get_db
from aura_backend.kb.project_store import store_project_file
from aura_backend.kb.search import get_project_file_content
from aura_backend.websocket.manager import manager
from aura_backend.websocket.schemas import WSMessage

logger = logging.getLogger(__name__)


async def read_project_file(project_name: str, path: str) -> str | None:
    """Read a project file from the KB store."""
    return await get_project_file_content(project_name, path)


async def write_project_file(
    project_name: str,
    path: str,
    content: str,
    language: str | None = None,
) -> dict:
    """Write a project file to the KB store and notify bridge clients."""
    result = await store_project_file(
        project_name=project_name,
        file_path=path,
        content=content,
        language=language,
    )

    # Broadcast to bridge clients so they can sync the file
    await manager.broadcast(
        WSMessage(
            type="project.file_write",
            payload={
                "project_name": project_name,
                "path": path,
                "content": content,
                "language": language,
            },
        )
    )

    return result


async def list_project_files(project_name: str) -> list[dict]:
    """List all files in a project."""
    db = get_db()
    rows = await db.query(
        "SELECT path, language, updated_at FROM kb_project_file WHERE project = $name ORDER BY path ASC",
        {"name": project_name},
    )
    return [
        {
            "path": r["path"],
            "language": r.get("language"),
            "updated_at": r.get("updated_at"),
        }
        for r in rows
    ]
