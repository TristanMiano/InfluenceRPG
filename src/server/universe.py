# src/server/universe.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from src.db import universe_db

router = APIRouter()

class UniverseCreateRequest(BaseModel):
    name: str = Field(..., description="Unique universe name")
    description: str = Field("", description="Optional description")

class UniverseResponse(BaseModel):
    id: str
    name: str
    description: str

@router.post("/universe/create", response_model=UniverseResponse)
def create_universe_endpoint(req: UniverseCreateRequest):
    try:
        uni = universe_db.create_universe(req.name, req.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create universe: {e}")
    return uni

@router.get("/universe/list", response_model=List[UniverseResponse])
def list_universes_endpoint():
    try:
        return universe_db.list_universes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list universes: {e}")
