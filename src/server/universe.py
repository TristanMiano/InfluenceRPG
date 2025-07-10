# src/server/universe.py

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from src.game.news_extractor import run_news_extractor
from src.db import universe_db

router = APIRouter()

class UniverseCreateRequest(BaseModel):
    name: str = Field(..., description="Unique universe name")
    description: str = Field("", description="Optional description")
    ruleset_id: str = Field(..., description="ID of the ruleset to use")

class UniverseResponse(BaseModel):
    id: str
    name: str
    description: str
    ruleset_id: str
    
class NewsResponse(BaseModel):
    id: int
    summary: str
    published_at: datetime
    
class ConflictResponse(BaseModel):
    id: int
    conflict_info: dict
    detected_at: datetime

class EventResponse(BaseModel):
    id: int
    game_id: str
    event_type: str
    event_payload: dict
    event_time: datetime

class GameBrief(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime

@router.post("/universe/create", response_model=UniverseResponse)
def create_universe_endpoint(req: UniverseCreateRequest):
    try:
        uni = universe_db.create_universe(req.name, req.description, req.ruleset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create universe: {e}")
    return uni

@router.get("/universe/list", response_model=List[UniverseResponse])
def list_universes_endpoint():
    try:
        return universe_db.list_universes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list universes: {e}")

@router.get("/universe/{universe_id}/news", response_model=List[NewsResponse])
def list_universe_news(universe_id: str):
    """
    Fetch the most recent news bulletins for a universe.
    """
    try:
        return universe_db.list_news(universe_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/universe/{universe_id}/news/publish")
def publish_universe_news(universe_id: str):
    """
    On-demand run of the news extractor for a universe.
    """
    try:
        summary = run_news_extractor(universe_id)
        return {"status": "ok", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/universe/{universe_id}/conflicts", response_model=List[ConflictResponse])
def list_universe_conflicts(universe_id: str):
    """
    Fetch recent hard conflicts for a universe.
    """
    try:
        return universe_db.list_conflicts(universe_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe/{universe_id}/events", response_model=List[EventResponse])
def list_universe_events(universe_id: str, limit: int = 100):
    """Return recent universe events for diagramming."""
    try:
        return universe_db.list_events(universe_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe/{universe_id}/games", response_model=List[GameBrief])
def list_universe_games(universe_id: str):
    """List games linked to a universe."""
    try:
        return universe_db.list_games_in_universe(universe_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

