# src/server/game.py
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from src.db import universe_db, game_db
from src.db.universe_db import get_universe
from src.db.character_db import get_character_by_id
from src.game.initial_prompt import generate_initial_scene

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

@router.post("/game/create", response_model=GameCreateResponse)
def create_game_endpoint(game_req: GameCreateRequest, request: Request):
    # Ensure user is authenticated
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Ensure character belongs to this user
    char = get_character_by_id(game_req.character_id)
    if not char or char.get("owner") != username:
        raise HTTPException(status_code=400, detail="Invalid character selection.")

    # Ensure character not in another active game
    if game_db.is_character_in_active_game(game_req.character_id):
        raise HTTPException(status_code=400, detail="Selected character is already in another game.")

    try:
        # Create the game
        new_game = game_db.create_game(game_req.name)

        # If universe specified, join it
        if game_req.universe_id:
            universe_db.add_game_to_universe(game_req.universe_id, new_game["id"])

        # Join creator’s character
        game_db.join_game(new_game["id"], game_req.character_id)

        # Generate and save opening scene
        player_name = char["name"]
        uni_name = None
        uni_desc = None
        ruleset_id = None
        if game_req.universe_id:
            uni = get_universe(game_req.universe_id)
            if uni:
                uni_name   = uni["name"]
                uni_desc   = uni["description"]
                ruleset_id = uni.get("ruleset_id")

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
def list_games_endpoint(request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        games = game_db.list_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"games": games}

@router.get("/game/{game_id}", response_model=GameCreateResponse)
def get_game_endpoint(game_id: str, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game

class CharacterInGameResponse(BaseModel):
    character_id: Optional[str] = None

@router.post("/game/{game_id}/join", response_model=GameCreateResponse)
def join_game_endpoint(game_id: str, join_req: GameJoinRequest, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    char = get_character_by_id(join_req.character_id)
    if not char or char.get("owner") != username:
        raise HTTPException(status_code=400, detail="Invalid character selection.")

    existing = game_db.get_character_for_user_in_game(game_id, username)
    if existing:
        if existing == join_req.character_id:
            return game_db.get_game(game_id)
        raise HTTPException(status_code=400, detail="You have already joined this game with a different character.")

    if game_db.is_character_in_active_game(join_req.character_id):
        raise HTTPException(status_code=400, detail="Selected character is already in another game.")
    try:
        game_db.join_game(game_id, join_req.character_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game

@router.get("/game/{game_id}/character", response_model=CharacterInGameResponse)
def get_user_character(game_id: str, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        char_id = game_db.get_character_for_user_in_game(game_id, username)
        return CharacterInGameResponse(character_id=char_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bound character: {e}")
