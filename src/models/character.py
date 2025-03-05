# src/models/character.py
from pydantic import BaseModel
from uuid import uuid4

class Character(BaseModel):
    id: str
    owner: str  # username of the owner
    name: str
    character_class: str
    # Additional attributes, stats, etc.

    @classmethod
    def create_new(cls, owner: str, name: str, character_class: str) -> "Character":
        return cls(id=str(uuid4()), owner=owner, name=name, character_class=character_class)
