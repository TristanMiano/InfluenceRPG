from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from src.server.main import templates

router = APIRouter()

# In-memory store of messages
_messages: List[Dict] = []

class Message(BaseModel):
    id: str
    sender: str
    recipient: str
    message: str
    timestamp: str
    read: bool = False

class MessageList(BaseModel):
    messages: List[Message]

class SendMessageRequest(BaseModel):
    recipient: str
    message: str

class MarkReadRequest(BaseModel):
    user: Optional[str] = None


def messages_page(request: Request, user: str | None = None):
    """Render the messages page and optional conversation."""
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)

    participants = set()
    for m in _messages:
        if m["sender"] == username:
            participants.add(m["recipient"])
        elif m["recipient"] == username:
            participants.add(m["sender"])

    conv = []
    if user:
        conv = [
            m
            for m in _messages
            if (m["sender"] == username and m["recipient"] == user)
            or (m["sender"] == user and m["recipient"] == username)
        ]
        conv.sort(key=lambda x: x["timestamp"])

    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "participants": sorted(participants),
            "with_user": user,
            "messages": conv,
        },
    )

@router.get("/messages", response_model=MessageList)
def list_messages(request: Request, user: str):
    """List messages in the conversation with the given user."""
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    conv = [m for m in _messages
            if (m["sender"] == username and m["recipient"] == user) or
               (m["sender"] == user and m["recipient"] == username)]
    conv.sort(key=lambda x: x["timestamp"])
    return {"messages": [Message(**m) for m in conv]}

@router.get("/messages/unread_count")
def unread_count(request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    count = sum(1 for m in _messages if m["recipient"] == username and not m["read"])
    return {"unread": count}

@router.post("/messages/send")
def send_message(data: SendMessageRequest, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    _messages.append({
        "id": str(uuid.uuid4()),
        "sender": username,
        "recipient": data.recipient,
        "message": data.message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "read": False
    })
    return {"status": "ok"}

@router.post("/messages/mark_read")
def mark_messages_read(data: MarkReadRequest, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    for m in _messages:
        if m["recipient"] == username and not m["read"]:
            if data.user is None or m["sender"] == data.user:
                m["read"] = True
    return {"status": "ok"}