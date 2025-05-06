# src/server/game_chat.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime
from src.db import game_db  
from src.llm.gm_llm import generate_gm_response
from src.db.character_db import get_character_by_id   

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
    # 1. Extract account & character IDs
    username     = websocket.query_params.get("username", "unknown")
    character_id = websocket.query_params.get("character_id", "unknown")

    # 2. Lookup the character’s name
    try:
        char = get_character_by_id(character_id)
        character_name = char["name"] if char else "unknown"
    except Exception:
        character_name = "unknown"

    # 3. Combine into a display name
    sender_display = f"{character_name} ({username})"

    # 4. Register this connection
    await manager.connect(game_id, websocket)

    # 5. Log & broadcast a “join” event for both players and GM context
    join_msg = f"{sender_display} has joined the game."
    system_entry = f"System: {join_msg}"
    conversation_histories.setdefault(game_id, []).append(system_entry)

    await manager.broadcast(game_id, json.dumps({
        "game_id": game_id,
        "sender": "System",
        "message": join_msg,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }))

    try:
        while True:
            data = await websocket.receive_text()
            stripped = data.strip()

            # --- Player message branch ---
            if not stripped.startswith("/gm"):
                # a) Persist & append to GM context
                game_db.save_chat_message(game_id, sender_display, data)
                conversation_histories[game_id].append(f"{sender_display}: {data}")

                # b) Broadcast to all players
                await manager.broadcast(game_id, json.dumps({
                    "game_id": game_id,
                    "sender": sender_display,
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }))

            # --- GM trigger branch ---
            else:
                # a) Form the prompt for the GM
                gm_prompt = stripped[3:].strip() or "Provide a narrative update."
                full_context = "\n".join(conversation_histories[game_id])

                # b) Ask the LLM
                gm_response = generate_gm_response(f"{full_context}\nUser (trigger): {gm_prompt}")

                # c) Record in DB + context
                game_db.save_chat_message(game_id, "GM", gm_response)
                conversation_histories[game_id].append(f"GM: {gm_response}")

                # d) Broadcast GM’s reply
                await manager.broadcast(game_id, json.dumps({
                    "game_id": game_id,
                    "sender": "GM",
                    "message": gm_response,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }))
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)

