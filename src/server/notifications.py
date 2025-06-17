from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict
import uuid

router = APIRouter()

# Simple in-memory notifications store: {username: [notification_dict]}
_notifications: Dict[str, List[Dict]] = {}

class Notification(BaseModel):
    id: str
    message: str
    read: bool = False

class NotificationList(BaseModel):
    notifications: List[Notification]

def add_notification(username: str, message: str) -> None:
    """Utility to add a notification for a user."""
    user_list = _notifications.setdefault(username, [])
    user_list.append({"id": str(uuid.uuid4()), "message": message, "read": False})

@router.get("/notifications", response_model=NotificationList)
def list_notifications(request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    items = [Notification(**n) for n in _notifications.get(username, [])]
    return {"notifications": items}

@router.post("/notifications/mark_read")
def mark_notifications_read(request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    for n in _notifications.get(username, []):
        n["read"] = True
    return {"status": "ok"}