# src/server/game_chat.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime

router = APIRouter()

# Import the in-memory characters database from the character module.
try:
    from src.server.character import characters_db
except ImportError:
    characters_db = {}

def get_character_name(username: str, character_id: str) -> str:
    """
    Given a username and a character_id, search the characters_db for the character's name.
    If not found, return the original character_id.
    """
    if username in characters_db:
        for char in characters_db[username]:
            # Assuming each character has an 'id' attribute.
            if char.id == character_id:
                return char.name
    return character_id

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
        if game_id in self.active_connections and websocket in self.active_connections[game_id]:
            self.active_connections[game_id].remove(websocket)

    async def broadcast(self, game_id: str, message: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                await connection.send_text(message)

manager = GameConnectionManager()

@router.websocket("/ws/game/{game_id}/chat")
async def game_chat_endpoint(game_id: str, websocket: WebSocket):
    """
    WebSocket endpoint for game chat.
    Clients must provide 'username' and 'character_id' as query parameters.
    Outgoing messages will display the sender as 'username::character_name'.
    """
    username = websocket.query_params.get("username", "unknown")
    character_id = websocket.query_params.get("character_id", "unknown")
    
    # Retrieve the character's name using the provided username and character_id.
    character_name = get_character_name(username, character_id)
    sender_display = f"{username}::{character_name}"
    
    await manager.connect(game_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_obj = {
                "game_id": game_id,
                "sender": sender_display,
                "message": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await manager.broadcast(game_id, json.dumps(message_obj))
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
