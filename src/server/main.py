# src/server/main.py
from fastapi import FastAPI, HTTPException, status, Request, Form
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

app = FastAPI(title="Influence RPG Prototype Server")

app.mount("/static", StaticFiles(directory="src/server/static"), name="static")

from src.server.game_chat import router as game_chat_router

# Include the game chat router without a prefix so that the paths remain unchanged.
app.include_router(game_chat_router)

templates = Jinja2Templates(directory="src/server/templates")

# Define login request and response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    role: str
    message: str

@app.post("/login", response_model=LoginResponse)
def login(request_data: LoginRequest):
    """
    Endpoint for user login.
    Verifies credentials and returns user information if valid.
    """
    user = authenticate_user(request_data.username, request_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return LoginResponse(username=user["username"], role=user["role"], message="Login successful")

# Serve the chat interface
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Serves the chat interface page.
    """
    return templates.TemplateResponse("index.html", {"request": request})
    
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

# Include the chat WebSocket router with prefix /chat
app.include_router(chat_router, prefix="/chat")
app.include_router(game_router, prefix="/api")
app.include_router(character_router)