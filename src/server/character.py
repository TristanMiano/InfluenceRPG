# src/server/character.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.db import character_db, game_db

router = APIRouter()

class CharacterCreateRequest(BaseModel):
    username: str
    name: str
    character_class: str = Field("default", description="One of your defined classes")
    character_data: Dict[str, Any] = Field(..., description="Full JSON blob of all stats/templates")

class CharacterResponse(BaseModel):
    id: str
    owner: str
    name: str
    character_class: str
    character_data: Dict[str, Any]
    
class AvailableCharacter(BaseModel):
    id:   str
    name: str

@router.post("/character/create", response_model=CharacterResponse)
def create_character_endpoint(req: CharacterCreateRequest):
    try:
        new_char = character_db.create_character(
            req.username,
            req.name,
            req.character_class,
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