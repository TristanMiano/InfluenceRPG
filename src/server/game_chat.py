# src/server/game_chat.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime
from src.db import game_db  # Import our new DB module
from src.llm.gm_llm import generate_gm_response

router = APIRouter()

# Global conversation history storage per game instance.
conversation_histories: Dict[str, List[str]] = {}

class GameConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)
        if game_id not in conversation_histories:
            conversation_histories[game_id] = []

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
    username = websocket.query_params.get("username", "unknown")
    character_id = websocket.query_params.get("character_id", "unknown")
    sender_display = f"{username}"
    
    await manager.connect(game_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            stripped_data = data.strip()
            
            # Save non-GM messages to the database.
            if not stripped_data.startswith("/gm"):
                game_db.save_chat_message(game_id, sender_display, data)
                conversation_histories[game_id].append(f"{sender_display}: {data}")
            
            if stripped_data.startswith("/gm"):
                gm_prompt = stripped_data[3:].strip() or "Provide a narrative update."
                conversation_context = "\n".join(conversation_histories[game_id])
                gm_response = generate_gm_response(f"{conversation_context}\nUser (trigger): {gm_prompt}")
                conversation_histories[game_id].append(f"GM: {gm_response}")
                game_db.save_chat_message(game_id, "GM", gm_response)
                message_obj = {
                    "game_id": game_id,
                    "sender": "GM",
                    "message": gm_response,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                await manager.broadcast(game_id, json.dumps(message_obj))
            else:
                message_obj = {
                    "game_id": game_id,
                    "sender": sender_display,
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                await manager.broadcast(game_id, json.dumps(message_obj))
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
