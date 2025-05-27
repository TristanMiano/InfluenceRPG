# src/server/character.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.db import character_db, game_db
from src.db.character_db import create_character as db_create_character, get_character_by_owner_and_universe
import logging

router = APIRouter()

class CharacterCreateRequest(BaseModel):
    username: str
    universe_id: str
    name: str
    character_data: Dict[str, Any]

class CharacterResponse(BaseModel):
    id: str
    owner: str
    universe_id: str
    name: str
    character_data: Dict[str, Any]
    
class AvailableCharacter(BaseModel):
    id:   str
    name: str

@router.post("/character/create", response_model=CharacterResponse)
def create_character_endpoint(req: CharacterCreateRequest):
    existing = get_character_by_owner_and_universe(req.username, req.universe_id)
    if existing:
        detail = "You already have a character in that universe."
        logging.warning(
            f"[character:create] 400 Bad Request – existing character: "
            f"username={req.username}, universe_id={req.universe_id}"
        )
        raise HTTPException(status_code=400, detail=detail)

    try:
        new_char = db_create_character(
            req.username,
            req.universe_id,
            req.name,
            req.character_data    
        )
    except HTTPException as he:
        # log any 4xx that you re-raise
        logging.error(f"[character:create] HTTPException: {he.detail}")
        raise
    except Exception as e:
        # catch-all for 5xx
        logging.exception(
            f"[character:create] 500 Error creating character: "
            f"username={req.username}, universe_id={req.universe_id}"
        )
        raise HTTPException(status_code=500, detail=f"Could not create character: {e}")
    return new_char


@router.get("/character/list", response_model=List[CharacterResponse])
def list_characters(username: str):
    try:
        chars = character_db.get_characters_by_owner(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list characters: {e}")
    return chars

@router.get("/character/list_available", response_model=List[AvailableCharacter])
def list_available_characters(username: str):
    """
    Return only the characters owned by `username` that are
    not already in another active (waiting/active) game.
    """
    try:
        all_chars = character_db.get_characters_by_owner(username)
        available = [
            AvailableCharacter(id=c["id"], name=c["name"])
            for c in all_chars
            if not game_db.is_character_in_active_game(c["id"])
        ]
        return available
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing available characters: {e}"
        )