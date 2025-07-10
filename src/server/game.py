# src/server/game.py
from fastapi import APIRouter, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from src.db import universe_db, game_db
from src.db.universe_db import get_universe
from src.db.character_db import get_character_by_id
from src.game.initial_prompt import generate_initial_scene
from src.game.brancher import run_branch
from src.server.notifications import notify_branch

router = APIRouter()

def _add_universe_names(game: dict) -> dict:
    """Return a new game dict with universe_names attached."""
    uni_ids = universe_db.list_universes_for_game(game["id"])
    names = []
    for uid in uni_ids:
        uni = get_universe(uid)
        if uni:
            names.append(uni["name"])
    game_with_names = dict(game)
    game_with_names["universe_names"] = names
    return game_with_names

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
    universe_names: List[str] = []

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

    return _add_universe_names(new_game)

@router.get("/game/list", response_model=GameListResponse)
def list_games_endpoint(
    request: Request,
    search: Optional[str] = Query(None),
    universe_id: Optional[str] = Query(None),
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        games = game_db.list_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filtered = []
    for g in games:
        uni_ids = universe_db.list_universes_for_game(g["id"])
        if universe_id and universe_id not in uni_ids:
            continue
        if search and search.lower() not in g["name"].lower():
            continue
        game_with_names = _add_universe_names(g)
        filtered.append(game_with_names)

    return {"games": filtered}

@router.get("/game/{game_id}", response_model=GameCreateResponse)
def get_game_endpoint(game_id: str, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return _add_universe_names(game)

class CharacterInGameResponse(BaseModel):
    character_id: Optional[str] = None

class BranchGroup(BaseModel):
    character_ids: List[str]
    description: str = ""

class BranchRequest(BaseModel):
    groups: List[BranchGroup]

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
            return _add_universe_names(game_db.get_game(game_id))
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
    return _add_universe_names(game)

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

class ChatMessage(BaseModel):
    sender: str
    message: str
    timestamp: str

class GameMessagesResponse(BaseModel):
    messages: List[ChatMessage]

@router.get("/game/{game_id}/messages", response_model=GameMessagesResponse)
def list_game_messages(game_id: str, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        msgs = game_db.list_chat_messages(game_id)
        serialized = [
            {
                "sender": msg["sender"],
                "message": msg["message"],
                "timestamp": msg["timestamp"].isoformat() + "Z",
            }
            for msg in msgs
        ]
        return {"messages": serialized}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/game/{game_id}/branch", response_model=List[GameCreateResponse])
def branch_game_endpoint(game_id: str, req: BranchRequest, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        players = set(game_db.list_players_in_game(game_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    assigned: set[str] = set()
    for grp in req.groups:
        if not grp.character_ids:
            raise HTTPException(status_code=400, detail="Each group must have at least one character")
        for cid in grp.character_ids:
            if cid not in players:
                raise HTTPException(status_code=400, detail=f"Character {cid} not in game")
            if cid in assigned:
                raise HTTPException(status_code=400, detail="Character assigned multiple times")
            assigned.add(cid)

    if assigned != players:
        raise HTTPException(status_code=400, detail="All characters must be assigned to one group")

    try:
        results = run_branch(game_id, [grp.dict() for grp in req.groups], send_notifications=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    notify_branch(game_id, results)

    enriched = []
    for r in results:
        g = _add_universe_names(r["game"])
        enriched.append(GameCreateResponse(**g))
    return enriched

@router.post("/game/{game_id}/close", response_model=GameCreateResponse)
def close_game_endpoint(game_id: str, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    game = game_db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    try:
        game_db.update_game_status(game_id, "closed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    game["status"] = "closed"
    return _add_universe_names(game)
