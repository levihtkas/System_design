from fastapi import WebSocket
from typing import List,Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, match_id: str):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, match_id: str):
        if match_id in self.active_connections:
            self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:  # Clean up empty match_id
                del self.active_connections[match_id]
    
    async def broadcast_to_match(self, match_id: str, message: str):
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                await connection.send_json(message)

manager = ConnectionManager()
