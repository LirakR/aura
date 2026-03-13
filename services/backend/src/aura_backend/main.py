from fastapi import FastAPI

from aura_backend.api.health import router as health_router
from aura_backend.config import settings
from aura_backend.websocket.router import router as ws_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
)

app.include_router(health_router)
app.include_router(ws_router)
