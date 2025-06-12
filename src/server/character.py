# src/server/character.py

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.db import character_db, game_db
from src.db.character_db import (
    create_character as db_create_character,
    get_character_by_owner_and_universe,
    get_characters_by_owner
)
import logging

router = APIRouter()

class CharacterCreateRequest(BaseModel):
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
def create_character_endpoint(req: CharacterCreateRequest, request: Request):
    # Ensure user is authenticated
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Prevent multiple characters per universe
    existing = get_character_by_owner_and_universe(username, req.universe_id)
    if existing:
        detail = "You already have a character in that universe."
        logging.warning(
            f"[character:create] 400 Bad Request – existing character: username={username}, universe_id={req.universe_id}"
        )
        raise HTTPException(status_code=400, detail=detail)

    try:
        new_char = db_create_character(
            owner=username,
            universe_id=req.universe_id,
            name=req.name,
            character_data=req.character_data    
        )
    except HTTPException as he:
        logging.error(f"[character:create] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logging.exception(
            f"[character:create] 500 Error creating character: username={username}, universe_id={req.universe_id}"
        )
        raise HTTPException(status_code=500, detail=f"Could not create character: {e}")
    return new_char


@router.get("/character/list", response_model=List[CharacterResponse])
def list_characters(request: Request):
    # Ensure user is authenticated
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        chars = get_characters_by_owner(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list characters: {e}")
    return chars

@router.get("/character/list_available", response_model=List[AvailableCharacter])
def list_available_characters(request: Request):
    # Ensure user is authenticated
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        all_chars = get_characters_by_owner(username)
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
