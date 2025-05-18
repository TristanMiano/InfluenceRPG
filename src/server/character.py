# src/server/character.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.db import character_db, game_db
from src.db.character_db import create_character as db_create_character, get_character_by_owner_and_universe

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
    # enforce one-per-universe (you already added this)
    existing = get_character_by_owner_and_universe(req.username, req.universe_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have a character in that universe."
        )

    try:
        new_char = db_create_character(
            req.username,
            req.universe_id,
            req.name,
            req.character_data    
        )
    except Exception as e:
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