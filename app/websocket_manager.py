from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, project_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[project_id].append(websocket)

    def disconnect(self, project_id: int, websocket: WebSocket) -> None:
        connections = self.active_connections.get(project_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and project_id in self.active_connections:
            del self.active_connections[project_id]

    async def broadcast(self, project_id: int, message: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []
        for websocket in self.active_connections.get(project_id, []):
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(project_id, websocket)


manager = ConnectionManager()
