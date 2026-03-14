"""Projects REST API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from aura_backend.db.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _record_to_str(val) -> str:
    return str(val)


@router.get("")
async def list_projects() -> list[dict]:
    db = get_db()
    rows = await db.query("SELECT * FROM kb_project ORDER BY name ASC")
    return [
        {
            "id": _record_to_str(r["id"]),
            "name": r["name"],
            "engine": r["engine"],
            "engine_version": r.get("engine_version"),
            "path": r.get("path"),
            "last_scan": r.get("last_scan"),
        }
        for r in rows
    ]


@router.get("/{project_id}")
async def get_project(project_id: str) -> dict:
    db = get_db()

    # Try by ID first, then by name
    rows = await db.query(
        "SELECT * FROM kb_project WHERE id = type::thing('kb_project', $pid)",
        {"pid": project_id},
    )
    if not rows:
        rows = await db.query(
            "SELECT * FROM kb_project WHERE name = $name",
            {"name": project_id},
        )
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")

    project = rows[0]
    project_name = project["name"]

    # Get file tree
    files = await db.query(
        "SELECT path, language, updated_at FROM kb_project_file WHERE project = $name ORDER BY path ASC",
        {"name": project_name},
    )

    return {
        "id": _record_to_str(project["id"]),
        "name": project_name,
        "engine": project["engine"],
        "engine_version": project.get("engine_version"),
        "path": project.get("path"),
        "last_scan": project.get("last_scan"),
        "files": [
            {
                "path": f["path"],
                "language": f.get("language"),
                "updated_at": f.get("updated_at"),
            }
            for f in files
        ],
    }
