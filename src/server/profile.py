# src/server/profile.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

# import the templates instance from main.py so asset_path and session username are available
from src.server.main import templates

from src.db.character_db import get_characters_by_owner
from src.db.game_db import list_games, get_character_for_user_in_game

router = APIRouter()

def _load_profile_data(owner: str) -> tuple[list[dict], list[dict]]:
    """Return characters and games for the given owner."""
    # 1) Fetch characters for owner
    try:
        characters = get_characters_by_owner(owner)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading characters: {e}")

     # 2) Fetch games containing one of the owner's characters
    try:
        all_games = list_games()
        user_games = []
        for g in all_games:
            char_id = get_character_for_user_in_game(g["id"], owner)
            if char_id:
                user_games.append(g)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading games: {e}")
    return characters, user_games


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)

    characters, user_games = _load_profile_data(username)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "profile_username": username,
            "is_self": True,
            "characters": characters,
            "games": user_games,
        },
    )


@router.get("/profile/{profile_username}", response_class=HTMLResponse)
def view_profile(profile_username: str, request: Request):
    """View another user's profile (requires login)."""
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)

    characters, user_games = _load_profile_data(profile_username)
    is_self = profile_username == username
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "profile_username": profile_username,
            "is_self": is_self,
            "characters": characters,
            "games": user_games
        }
    )
