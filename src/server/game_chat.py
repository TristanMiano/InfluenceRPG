#!/usr/bin/env python3
"""
game_chat.py - WebSocket endpoint for game chat with integrated GM LLM functionality

This version of the game chat endpoint maintains a conversation history per game instance.
If a chat message starts with '/gm', it triggers the GM LLM to generate a narrative response
using the full conversation context. The GM response is then broadcast to all clients in the game.
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime
from src.llm.gm_llm import generate_gm_response

router = APIRouter()

# Global conversation history storage per game instance.
conversation_histories: Dict[str, List[str]] = {}

class GameConnectionManager:
    """
    Manages active WebSocket connections for game instances.
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)
        # Initialize conversation history if not already present.
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
    """
    WebSocket endpoint for game chat.
    
    Clients must provide 'username' and 'character_id' as query parameters.
    Outgoing messages are structured with a sender label.
    
    Special Command:
      - Messages starting with '/gm' trigger a GM narrative response.
    """
    username = websocket.query_params.get("username", "unknown")
    character_id = websocket.query_params.get("character_id", "unknown")
    
    # For now, the sender display is simply the username.
    sender_display = f"{username}"
    
    await manager.connect(game_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            stripped_data = data.strip()
            
            # If it's not a GM trigger, add it to the conversation history.
            if not stripped_data.startswith("/gm"):
                conversation_histories[game_id].append(f"{sender_display}: {data}")
            
            # Check if message is a GM trigger.
            if stripped_data.startswith("/gm"):
                # Extract optional GM prompt after the command.
                gm_prompt = stripped_data[3:].strip() or "Provide a narrative update."
                # Combine conversation history into a single context string.
                conversation_context = "\n".join(conversation_histories[game_id])
                # Generate the GM response using the GM LLM module.
                gm_response = generate_gm_response(f"{conversation_context}\nUser (trigger): {gm_prompt}")
                # Append GM response to the conversation history.
                conversation_histories[game_id].append(f"GM: {gm_response}")
                # Build the structured message object.
                message_obj = {
                    "game_id": game_id,
                    "sender": "GM",
                    "message": gm_response,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                await manager.broadcast(game_id, json.dumps(message_obj))
            else:
                # Regular message broadcasting.
                message_obj = {
                    "game_id": game_id,
                    "sender": sender_display,
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                await manager.broadcast(game_id, json.dumps(message_obj))
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
