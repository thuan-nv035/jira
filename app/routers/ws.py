from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.deps import get_user_from_token, require_project_member
from app.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/projects/{project_id}")
async def project_socket(websocket: WebSocket, project_id: int, token: str | None = None):
    async with AsyncSessionLocal() as db:  # type: AsyncSession
        user = await get_user_from_token(db, token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        try:
            await require_project_member(db, project_id, user.id)
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect(project_id, websocket)
    await websocket.send_json({"event": "socket.connected", "data": {"project_id": project_id}})

    try:
        while True:
            # Keep connection alive. Client can send {"event":"ping"}; server replies pong.
            data = await websocket.receive_json()
            if data.get("event") == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
    except Exception:
        manager.disconnect(project_id, websocket)
