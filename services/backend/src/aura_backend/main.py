import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aura_backend.api.chat import router as chat_router
from aura_backend.api.health import router as health_router
from aura_backend.api.kb import router as kb_router
from aura_backend.api.projects import router as projects_router
from aura_backend.config import settings
from aura_backend.db.connection import close_db, init_db
from aura_backend.db.schema import apply_schema
from aura_backend.embeddings.service import close_embeddings, init_embeddings
from aura_backend.websocket.router import router as ws_router

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)


async def _background_ingest():
    """Run KB ingestion in the background so the server can serve requests."""
    try:
        from aura_backend.kb.docs_fetcher import fetch_godot_docs
        from aura_backend.kb.engine_ingest import ingest_engine_docs

        docs_path = await fetch_godot_docs(
            settings.kb_godot_version, settings.kb_docs_cache_dir
        )
        await ingest_engine_docs(docs_path, "godot", settings.kb_godot_version)
    except Exception:
        logger.error("Background auto-ingest failed — KB may be empty", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────
    await init_db()
    from aura_backend.db.connection import get_db

    await apply_schema(get_db())

    await init_embeddings()

    # Auto-ingest engine docs in the background so the server starts immediately
    ingest_task = None
    if settings.kb_auto_ingest:
        logger.info("Starting KB auto-ingest in background …")
        ingest_task = asyncio.create_task(_background_ingest())

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    if ingest_task and not ingest_task.done():
        logger.info("Waiting for background ingest to finish before shutdown …")
        ingest_task.cancel()
        try:
            await ingest_task
        except asyncio.CancelledError:
            logger.info("Background ingest cancelled")
    from aura_backend.agent.service import shutdown_provider_service

    await shutdown_provider_service()
    await close_embeddings()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(kb_router)
app.include_router(chat_router)
app.include_router(projects_router)
app.include_router(ws_router)
