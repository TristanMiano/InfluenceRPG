# src/server/game.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from src.db import game_db
from src.game.initial_prompt import generate_initial_scene
from psycopg2.errors import UniqueViolation

router = APIRouter()

class GameCreateRequest(BaseModel):
    name: str
    initial_details: str

class GameCreateResponse(BaseModel):
    id: str
    name: str
    status: str

class GameListResponse(BaseModel):
    games: List[GameCreateResponse]

class GameJoinRequest(BaseModel):
    character_id: str

@router.post("/game/create", response_model=GameCreateResponse)
def create_game_endpoint(game_req: GameCreateRequest):
    try:
        new_game = game_db.create_game(game_req.name)
        opening_scene = generate_initial_scene(game_req.initial_details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return new_game

@router.get("/game/list", response_model=GameListResponse)
def list_games_endpoint():
    try:
        games = game_db.list_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"games": games}

@router.get("/game/{game_id}", response_model=GameCreateResponse)
def get_game_endpoint(game_id: str):
    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game

@router.post("/game/{game_id}/join", response_model=GameCreateResponse)
def join_game_endpoint(game_id: str, join_req: GameJoinRequest):
    try:
        # Try to insert the (game_id, character_id) pair
        game_db.join_game(game_id, join_req.character_id)
    except UniqueViolation:
        # Already joined — ignore so they can re-enter the chat
        pass
    except Exception as e:
        # Other errors bubble up as 500
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch and return the game details
    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

