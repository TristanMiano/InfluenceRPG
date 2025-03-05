# src/server/game_chat.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime

router = APIRouter()

# Manage connections per game instance:
class GameConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.active_connections:
            if websocket in self.active_connections[game_id]:
                self.active_connections[game_id].remove(websocket)

    async def broadcast(self, game_id: str, message: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                await connection.send_text(message)

manager = GameConnectionManager()

@router.websocket("/ws/game/{game_id}/chat")
async def game_chat_endpoint(game_id: str, websocket: WebSocket):
    """
    WebSocket endpoint for chat within a specific game instance.
    Clients must pass a 'character_id' query parameter.
    """
    character_id = websocket.query_params.get("character_id", "unknown")
    await manager.connect(game_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_obj = {
                "game_id": game_id,
                "character_id": character_id,
                "message": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await manager.broadcast(game_id, json.dumps(message_obj))
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
