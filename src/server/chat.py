# src/server/chat.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the chat interface.
    Clients connect to this endpoint (with a 'username' query parameter)
    to send and receive chat messages.
    """
    # Get the username from the query parameters (default to "unknown" if not provided)
    username = websocket.query_params.get("username", "unknown")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Build a structured message object
            message_obj = {
                "sender": username,
                "message": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            # Broadcast the JSON string to all connections.
            await manager.broadcast(json.dumps(message_obj))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
