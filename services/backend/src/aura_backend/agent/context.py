"""Build turn context from project files via hybrid KB search."""

from __future__ import annotations

import logging

from aura_backend.config import settings
from aura_backend.kb.search import hybrid_search

logger = logging.getLogger(__name__)


async def build_turn_context(
    project: str,
    user_message: str,
    budget: int | None = None,
) -> str | None:
    """Search KB for project files relevant to the user message.

    Returns a formatted context string within the token budget,
    or None if nothing relevant was found.
    """
    budget = budget or settings.agent_context_budget

    try:
        results = await hybrid_search(
            user_message,
            scope="project",
            project=project,
            limit=10,
        )
    except Exception:
        logger.warning("Context search failed for project %s", project, exc_info=True)
        return None

    if not results:
        return None

    lines: list[str] = []
    chars = 0

    for r in results:
        path = r.get("path", "unknown")
        # Try to get content summary
        search_text = r.get("search_text", "")
        snippet = search_text[:500] if search_text else ""

        entry = f"--- {path} ---\n{snippet}\n"
        if chars + len(entry) > budget:
            break
        lines.append(entry)
        chars += len(entry)

    if not lines:
        return None

    header = f"[Relevant project files for context — project: {project}]\n\n"
    return header + "\n".join(lines)
