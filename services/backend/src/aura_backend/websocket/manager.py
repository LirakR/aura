import uuid

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from aura_backend.config import settings
from aura_backend.websocket.schemas import (
    ConnectionAckPayload,
    WSMessage,
)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._engine_clients: set[str] = set()

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self._connections[client_id] = websocket

        ack = WSMessage(
            type="connection.ack",
            payload=ConnectionAckPayload(
                clientId=client_id,
                serverVersion=settings.version,
            ).model_dump(),
        )
        await websocket.send_json(ack.model_dump())
        return client_id

    def disconnect(self, client_id: str) -> None:
        self._connections.pop(client_id, None)
        self._engine_clients.discard(client_id)

    def is_engine(self, client_id: str) -> bool:
        return client_id in self._engine_clients

    async def broadcast(self, message: WSMessage, exclude: str | None = None) -> None:
        data = message.model_dump()
        stale: list[str] = []
        for client_id, ws in self._connections.items():
            if client_id == exclude:
                continue
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(data)
            except Exception:
                stale.append(client_id)
        for cid in stale:
            self.disconnect(cid)

    async def broadcast_engine_status(self, message: WSMessage, sender_id: str) -> None:
        """Broadcast real engine status to all non-engine clients."""
        self._engine_clients.add(sender_id)
        await self.broadcast(message, exclude=sender_id)

    async def send_to(self, client_id: str, message: WSMessage) -> None:
        ws = self._connections.get(client_id)
        if ws and ws.client_state == WebSocketState.CONNECTED:
            await ws.send_json(message.model_dump())


manager = ConnectionManager()
