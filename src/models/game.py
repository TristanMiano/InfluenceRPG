# src/models/game.py
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4

class Game(BaseModel):
    id: str
    name: str
    players: List[str] = []  # List of character IDs
    status: str = "waiting"  # Could be waiting, active, finished, etc.

    @classmethod
    def create_new(cls, name: str) -> "Game":
        return cls(id=str(uuid4()), name=name)
