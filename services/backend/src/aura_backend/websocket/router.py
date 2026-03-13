from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from aura_backend.websocket.manager import manager
from aura_backend.websocket.schemas import WSMessage

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

    except WebSocketDisconnect:
        was_engine = manager.is_engine(client_id)
        manager.disconnect(client_id)
        if was_engine:
            msg = WSMessage(type="engine.disconnect")
            await manager.broadcast(msg)
