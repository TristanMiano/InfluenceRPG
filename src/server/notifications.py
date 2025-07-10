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
    
def notify_game_advanced(game_id: str, triggering_user: str) -> None:
    """Send a notification to all other players in the game."""
    from src.db.game_db import list_players_in_game, get_game
    from src.db.character_db import get_character_by_id

    try:
        game = get_game(game_id)
        game_name = game["name"] if game else game_id
    except Exception:
        game_name = game_id

    player_ids = list_players_in_game(game_id)
    notified = set()
    for cid in player_ids:
        char = get_character_by_id(cid)
        if not char:
            continue
        owner = char.get("owner")
        if owner and owner != triggering_user and owner not in notified:
            notified.add(owner)
            add_notification(
                owner,
                f'Game "{game_name}" advanced via /gm command.'
            )

def notify_branch(original_game_id: str, branch_results: List[dict]) -> None:
    """Notify players which new game they are in after a branch."""
    from src.db.character_db import get_character_by_id
    from src.db.game_db import get_game

    try:
        orig = get_game(original_game_id)
        base_name = orig["name"] if orig else original_game_id
    except Exception:
        base_name = original_game_id

    for res in branch_results:
        new_game = res.get("game")
        if not new_game:
            continue
        new_name = new_game.get("name", "")
        for cid in res.get("character_ids", []):
            char = get_character_by_id(cid)
            if not char:
                continue
            owner = char.get("owner")
            if owner:
                add_notification(
                    owner,
                    f'Game "{base_name}" branched. You are now in "{new_name}".'
                )