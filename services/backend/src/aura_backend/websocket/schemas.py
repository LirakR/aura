from datetime import datetime, timezone

from pydantic import BaseModel, Field


class WSMessage(BaseModel):
    type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict = Field(default_factory=dict)


class ConnectionAckPayload(BaseModel):
    clientId: str
    serverVersion: str
