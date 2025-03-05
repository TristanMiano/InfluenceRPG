# src/server/main.py
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.auth.auth import authenticate_user
from src.models.user import User
from src.server.chat import router as chat_router
from src.server.game import router as game_router

app = FastAPI(title="Tabletop RPG Prototype Server")

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

# Include the chat WebSocket router with prefix /chat
app.include_router(chat_router, prefix="/chat")
app.include_router(game_router, prefix="/api")
