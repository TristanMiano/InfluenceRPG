from typing import Optional
from fastapi import FastAPI, HTTPException, status, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.auth.auth import authenticate_user, get_db_connection
from src.utils.security import hash_password
from src.models.user import User
from src.server.chat import router as chat_router
from src.server.game import router as game_router
from src.server.character import router as character_router
from src.server.universe import router as universe_router
import asyncio
from src.db import universe_db
from src.game.news_extractor import run_news_extractor

app = FastAPI(title="Influence RPG Prototype Server")

# Serve static files
app.mount("/static", StaticFiles(directory="src/server/static"), name="static")

templates = Jinja2Templates(directory="src/server/templates")

# Include routers
from src.server.game_chat import router as game_chat_router
app.include_router(game_chat_router)
app.include_router(chat_router, prefix="/chat/ws")  # WebSocket chat
app.include_router(game_router, prefix="/api")
app.include_router(character_router)
app.include_router(universe_router, prefix="/api")

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
                    print("Error in scheduled news:", e)
            await asyncio.sleep(30 * 60)  # 30 minutes

    asyncio.create_task(news_loop())

# Login models
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
def login(request_data: LoginRequest):
    user = authenticate_user(request_data.username, request_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return LoginResponse(username=user["username"], role=user["role"], message="Login successful")

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
    # Basic validation
    if password != password2:
        return templates.TemplateResponse(
            "create_account.html",
            {"request": request, "error": "Passwords do not match."},
            status_code=400
        )

    conn = get_db_connection()
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

    # On success, redirect back to login
    return RedirectResponse(url="/", status_code=302)

@app.get("/lobby", response_class=HTMLResponse)
def read_lobby(request: Request, username: str = Query(...)):
    # Render the lobby page
    return templates.TemplateResponse(
        "lobby.html", {"request": request, "username": username}
    )

from src.db.universe_db import list_universes_for_game  # add this import

@app.get("/chat", response_class=HTMLResponse)
def read_chat(
    request: Request,
    username: str = Query(...),
    game_id: str = Query(...),
    character_id: Optional[str] = Query(None),
    universe_id: Optional[str] = Query(None),
):
    """
    Render chat page or auto-redirect if character already tied to this game.
    If no universe_id is passed, look it up from the DB.
    """
    # 1) If no character specified, redirect to the full URL
    if not character_id:
        from src.db.game_db import get_character_for_user_in_game
        char_id = get_character_for_user_in_game(game_id, username)
        if char_id:
            # Rebuild /chat URL, preserving universe_id if it was there
            redirect_url = (
                f"/chat?username={username}"
                f"&game_id={game_id}"
                f"&character_id={char_id}"
            )
            if universe_id:
                redirect_url += f"&universe_id={universe_id}"
            return RedirectResponse(url=redirect_url)
        return RedirectResponse(url=f"/lobby?username={username}")

    # 2) If we still don’t have a universe_id, fetch it from the DB
    if not universe_id:
        try:
            ulist = list_universes_for_game(game_id)
            if ulist:
                universe_id = ulist[0]
        except Exception:
            universe_id = None

    # 3) Render the chat page, passing the (possibly looked-up) universe_id
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "username": username,
            "game_id": game_id,
            "character_id": character_id,
            "universe_id": universe_id or "",
        },
    )



@app.get("/character/new", response_class=HTMLResponse)
def read_character_create(request: Request, username: str = Query(...)):
    """
    Render the standalone character‐creation form.
    """
    return templates.TemplateResponse(
        "character_create.html",
        {"request": request, "username": username}
    )

@app.get("/game/new", response_class=HTMLResponse)
def read_game_create(
    request: Request,
    username: str = Query(...),
    universe_id: str | None = Query(None),
):
    """
    Render the standalone game‐creation form, optionally pre‐selecting a universe.
    """
    return templates.TemplateResponse(
        "game_creation.html",
        {"request": request, "username": username, "universe_id": universe_id}
    )
    
@app.get("/universe/new", response_class=HTMLResponse)
def read_universe_create(request: Request, username: str = Query(...)):
    return templates.TemplateResponse(
        "universe_create.html",
        {"request": request, "username": username}
    )
