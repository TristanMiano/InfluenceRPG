# src/server/profile.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

# import the templates instance from main.py so asset_path and session username are available
from src.server.main import templates

from src.db.character_db import get_characters_by_owner
from src.db.game_db import list_games, get_character_for_user_in_game

router = APIRouter()

@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    # Ensure user is authenticated via session
    username = request.session.get("username")
    if not username:
        # Redirect to login
        return RedirectResponse(url="/", status_code=302)

    # 1) Fetch their characters
    try:
        characters = get_characters_by_owner(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading characters: {e}")

    # 2) Fetch all games and filter those they’re in
    try:
        all_games = list_games()
        user_games = []
        for g in all_games:
            char_id = get_character_for_user_in_game(g["id"], username)
            if char_id:
                user_games.append(g)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading games: {e}")

    # 3) Render template with context
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "characters": characters,
            "games": user_games
        }
    )
