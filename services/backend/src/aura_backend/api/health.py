from fastapi import APIRouter

from aura_backend.config import settings

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": settings.version}
