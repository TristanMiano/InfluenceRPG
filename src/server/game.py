# src/server/game.py
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from src.db import universe_db, game_db
from src.db.universe_db import get_universe
from src.db.character_db import get_character_by_id
from src.game.initial_prompt import generate_initial_scene
from psycopg2.errors import UniqueViolation

router = APIRouter()

class GameCreateRequest(BaseModel):
    name: str
    character_id: str
    universe_id: Optional[str] = Field(
        None, description="If set, new game will be joined into this universe"
    )
    initial_details: str = Field(..., description="User-provided setup details")
    setup_prompt: Optional[str] = Field(
        None, description="Full RAG-assembled prompt to feed into the GM LLM"
    )

class GameCreateResponse(BaseModel):
    id: str
    name: str
    status: str

class GameListResponse(BaseModel):
    games: List[GameCreateResponse]

class GameJoinRequest(BaseModel):
    character_id: str
    username: str  # to enforce one character per user per game

@router.post("/game/create", response_model=GameCreateResponse)
def create_game_endpoint(game_req: GameCreateRequest):
    # 1) Ensure character not in another active game
    if game_db.is_character_in_active_game(game_req.character_id):
        raise HTTPException(status_code=400, detail="Selected character is already in another game.")
    try:
        # 2) Create the game
        new_game = game_db.create_game(game_req.name)

        # 3) If universe specified, join it
        if game_req.universe_id:
            universe_db.add_game_to_universe(game_req.universe_id, new_game["id"])

        # 4) Join creator’s character
        game_db.join_game(new_game["id"], game_req.character_id)

        # 5) Generate opening scene, save to chat
        # 1) Look up starting player's character name
        char = get_character_by_id(game_req.character_id)
        player_name = char["name"] if char else "Unknown"

        # After you fetch uni (with get_universe), uni will now include ruleset_id
        uni_name = None
        uni_desc = None
        ruleset_id = None
        if game_req.universe_id:
            uni = get_universe(game_req.universe_id)
            if uni:
                uni_name     = uni["name"]
                uni_desc     = uni["description"]
                ruleset_id   = uni.get("ruleset_id")

        opening_scene = generate_initial_scene(
            initial_details=game_req.setup_prompt or "",
            game_name=new_game["name"],
            universe_name=uni_name,
            universe_description=uni_desc,
            starting_player=player_name,
            ruleset_id=ruleset_id
        )
        
        game_db.save_chat_message(new_game["id"], "GM", opening_scene)
    except HTTPException:
        raise
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
    # 1. Ensure user hasn't already joined with another character
    existing = game_db.get_character_for_user_in_game(game_id, join_req.username)
    if existing:
        if existing == join_req.character_id:
            # Idempotent re-join
            return game_db.get_game(game_id)
        raise HTTPException(status_code=400, detail="You have already joined this game with a different character.")
    # 2. Prevent character being in another game
    if game_db.is_character_in_active_game(join_req.character_id):
        raise HTTPException(status_code=400, detail="Selected character is already in another game.")
    try:
        game_db.join_game(game_id, join_req.character_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch and return the game details
    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

class CharacterInGameResponse(BaseModel):
    character_id: Optional[str] = None

@router.get("/game/{game_id}/character", response_model=CharacterInGameResponse)
def get_user_character(game_id: str, username: str = Query(...)):
    """
    Returns the character_id that `username` has already joined with in this game,
    or null if they’ve never joined.
    """
    try:
        char_id = game_db.get_character_for_user_in_game(game_id, username)
        return CharacterInGameResponse(character_id=char_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching bound character: {e}"
        )
