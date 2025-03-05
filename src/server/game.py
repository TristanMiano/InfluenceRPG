# src/server/game.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from src.models.game import Game
from src.models.character import Character  # For future use if needed

router = APIRouter()

# In-memory storage for game instances.
games_db = {}

# Pydantic models for game creation, listing, and joining.

class GameCreateRequest(BaseModel):
    name: str

class GameCreateResponse(BaseModel):
    id: str
    name: str
    status: str

class GameListResponse(BaseModel):
    games: List[GameCreateResponse]

class GameJoinRequest(BaseModel):
    character_id: str

@router.post("/game/create", response_model=GameCreateResponse)
def create_game(game_req: GameCreateRequest):
    """
    Create a new game instance with a given name.
    Returns the game ID, name, and current status.
    """
    new_game = Game.create_new(game_req.name)
    games_db[new_game.id] = new_game
    return GameCreateResponse(id=new_game.id, name=new_game.name, status=new_game.status)

@router.get("/game/list", response_model=GameListResponse)
def list_games():
    """
    List all available game instances.
    """
    game_list = [
        GameCreateResponse(id=game.id, name=game.name, status=game.status)
        for game in games_db.values()
    ]
    return GameListResponse(games=game_list)

@router.get("/game/{game_id}", response_model=GameCreateResponse)
def get_game(game_id: str):
    """
    Retrieve details for a specific game instance.
    """
    game = games_db.get(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return GameCreateResponse(id=game.id, name=game.name, status=game.status)

@router.post("/game/{game_id}/join", response_model=GameCreateResponse)
def join_game(game_id: str, join_req: GameJoinRequest):
    """
    Add a character (by character_id) to the game instance's players list.
    For this prototype, simply store the character_id in the game.
    """
    game = games_db.get(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    
    if join_req.character_id not in game.players:
        game.players.append(join_req.character_id)
    
    return GameCreateResponse(id=game.id, name=game.name, status=game.status)
