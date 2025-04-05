# src/server/character.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src.db import character_db  # Import the new DB module

router = APIRouter()

class CharacterCreateRequest(BaseModel):
    username: str
    name: str
    character_class: str = "default"

class CharacterResponse(BaseModel):
    id: str
    owner: str
    name: str
    character_class: str

@router.post("/character/create", response_model=CharacterResponse)
def create_character_endpoint(req: CharacterCreateRequest):
    try:
        new_character = character_db.create_character(req.username, req.name, req.character_class)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return new_character

@router.get("/character/list", response_model=List[CharacterResponse])
def list_characters(username: str):
    try:
        characters = character_db.get_characters_by_owner(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return characters
