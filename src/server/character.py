from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src.models.character import Character

router = APIRouter()

# In-memory storage mapping usernames to a list of Character objects.
characters_db = {}

class CharacterCreateRequest(BaseModel):
    username: str
    name: str
    character_class: str = "default"  # For now, a default value is used.

class CharacterResponse(BaseModel):
    id: str
    owner: str
    name: str
    character_class: str

@router.post("/character/create", response_model=CharacterResponse)
def create_character(req: CharacterCreateRequest):
    new_character = Character.create_new(owner=req.username, name=req.name, character_class=req.character_class)
    if req.username in characters_db:
        characters_db[req.username].append(new_character)
    else:
        characters_db[req.username] = [new_character]
    return new_character

@router.get("/character/list", response_model=List[CharacterResponse])
def list_characters(username: str):
    return characters_db.get(username, [])
