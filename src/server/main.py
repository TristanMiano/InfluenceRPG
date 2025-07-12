import os
from pathlib import Path
from typing import Optional
import json
import logging
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
# Import the base Jinja2Templates so we can subclass it
from fastapi.templating import Jinja2Templates as _Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from src.auth import auth
from src.utils.security import hash_password
from src.models.user import User
from src.server.chat import router as chat_router
from src.server.game import router as game_router
from src.server.character import router as character_router
from src.server.universe import router as universe_router
from src.server.ruleset import router as ruleset_router
from src.server.game_setup import router as setup_router
from src.server.character_wizard import router as character_wizard_router
from src.server.game_chat import router as game_chat_router

from src.db import universe_db
from src.game.news_extractor import run_news_extractor

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(title="Influence RPG Prototype Server")

# Mount static files for fingerprinted assets
app.mount(
    "/static",
    StaticFiles(directory="dist/static", html=False),
    name="static",
)

# Set up session middleware 
SESSION_SECRET = os.getenv("SESSION_SECRET", "CHANGE_ME")
if SESSION_SECRET == "CHANGE_ME":
    logging.warning("SESSION_SECRET is using default; override in environment.")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET
)

# Subclass Jinja2Templates to automatically inject session username
class Jinja2TemplatesWithSession(_Jinja2Templates):
    def TemplateResponse(self, name: str, context: dict, **kwargs):
        request: Request = context.get('request')
        if request:
            # Inject 'username' into the template context from session
            context.setdefault('username', request.session.get('username'))
        return super().TemplateResponse(name, context, **kwargs)

# Set up Jinja2 templates with session support
templates = Jinja2TemplatesWithSession(directory="src/server/templates")

# Load Vite manifest for asset paths
_manifest_path = Path("dist/static/.vite/manifest.json")
_manifest = json.loads(_manifest_path.read_text())

# Expose asset_path function to templates
templates.env.globals["asset_path"] = lambda name: (
    _manifest.get(name, {}).get("file") or
    next((v.get("file") for k, v in _manifest.items() if k.endswith(f"/{name}") and isinstance(v, dict)), None)
)

from src.server.profile import router as profile_router
from src.server.account import router as account_router
from src.server.notifications import router as notifications_router
from src.server.messages import router as messages_router

# Include routers
app.include_router(game_chat_router)
app.include_router(chat_router, prefix="/chat/ws")  # WebSocket chat
app.include_router(game_router, prefix="/api")
app.include_router(character_router)
app.include_router(universe_router, prefix="/api")
app.include_router(ruleset_router)
app.include_router(character_wizard_router)
app.include_router(setup_router)
app.include_router(notifications_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(profile_router)
app.include_router(account_router)

logging.info(f"Session secret loaded: {'SET' if SESSION_SECRET != 'CHANGE_ME' else 'DEFAULT'}")


@app.on_event("startup")
async def start_periodic_news_loop():
    """
    Every 30 minutes, run news extractor for all universes.
    """
    async def news_loop():
        while True:
            universes = universe_db.list_universes()
            for uni in universes:
                try:
                    run_news_extractor(uni["id"])
                except Exception as e:
                    logging.error(f"Error in scheduled news for {uni['id']}: {e}")
            await asyncio.sleep(30 * 60)

    asyncio.create_task(news_loop())


# Models for login
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    role: str
    message: str


@app.get("/", response_class=HTMLResponse)
def read_login(request: Request):
    # Render the login page
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_model=LoginResponse)
def login(request_data: LoginRequest, request: Request):
    user = auth.authenticate_user(request_data.username, request_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    request.session["username"] = user["username"]
    return LoginResponse(username=user["username"], role=user["role"], message="Login successful")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


@app.get("/create-account", response_class=HTMLResponse)
def create_account_form(request: Request):
    return templates.TemplateResponse("create_account.html", {"request": request, "error": None})

@app.post("/create-account", response_class=HTMLResponse)
async def create_account_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...)
):
    if password != password2:
        return templates.TemplateResponse(
            "create_account.html",
            {"request": request, "error": "Passwords do not match."},
            status_code=400
        )
    conn = auth.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return templates.TemplateResponse(
                    "create_account.html",
                    {"request": request, "error": f"Username '{username}' is already taken."},
                    status_code=400
                )
            cur.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
                (username, hash_password(password), "player")
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        return templates.TemplateResponse(
            "create_account.html",
            {"request": request, "error": f"Error creating account: {e}"},
            status_code=500
        )
    finally:
        conn.close()
    return RedirectResponse(url="/", status_code=302)


@app.get("/lobby", response_class=HTMLResponse)
def read_lobby(request: Request, game_id: Optional[str] = Query(None)):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "lobby.html", {"request": request}
    )


@app.get("/chat", response_class=HTMLResponse)
def read_chat(
    request: Request,
    game_id: str = Query(...),
    character_id: Optional[str] = Query(None),
    universe_id: Optional[str] = Query(None),
):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    from src.db.game_db import get_character_for_user_in_game
    if not character_id:
        char_id = get_character_for_user_in_game(game_id, username)
        if char_id:
            url = f"/chat?game_id={game_id}&character_id={char_id}"
            if universe_id:
                url += f"&universe_id={universe_id}"
            return RedirectResponse(url)
        return RedirectResponse("/lobby")
    if not universe_id:
        uni_list = universe_db.list_universes_for_game(game_id)
        if uni_list:
            url = f"/chat?game_id={game_id}&character_id={character_id}&universe_id={uni_list[0]}"
            return RedirectResponse(url)
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "game_id": game_id,
            "character_id": character_id,
            "universe_id": universe_id or "",
        },
    )


@app.get("/character/new", response_class=HTMLResponse)
def read_character_create(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "character_create.html", {"request": request}
    )


@app.get("/game/new", response_class=HTMLResponse)
def read_game_create(
    request: Request,
    universe_id: Optional[str] = Query(None),
):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    context = {"request": request}
    if universe_id:
        context["universe_id"] = universe_id
    return templates.TemplateResponse(
        "game_creation.html",
        context
    )


@app.get("/universe/new", response_class=HTMLResponse)
def read_universe_create(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "universe_create.html", {"request": request}
    )


@app.get("/universes", response_class=HTMLResponse)
def read_universes_page(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "universes.html",
        {"request": request}
    )
