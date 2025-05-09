# src/server/character.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.db import character_db

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
