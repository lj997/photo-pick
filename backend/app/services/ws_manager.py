"""
WebSocket 连接管理器

维护每个会话的 WebSocket 连接列表，提供广播方法。
自动清理断开的连接。
"""
import json
from fastapi import WebSocket


class WSManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(ws)

    def disconnect(self, session_id: str, ws: WebSocket):
        if session_id in self.connections:
            self.connections[session_id].remove(ws)
            if not self.connections[session_id]:
                del self.connections[session_id]

    async def broadcast(self, session_id: str, msg_type: str, data: dict):
        if session_id not in self.connections:
            return
        message = json.dumps({"type": msg_type, "data": data})
        dead = []
        for ws in self.connections[session_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections[session_id].remove(ws)


ws_manager = WSManager()
