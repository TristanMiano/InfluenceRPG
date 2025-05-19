from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from src.db.ruleset_db import create_ruleset, list_rulesets, get_ruleset

router = APIRouter(prefix="/api/ruleset", tags=["ruleset"])

class RulesetCreateRequest(BaseModel):
    name: str = Field(..., description="Unique ruleset name")
    description: str = Field("", description="Optional description")
    full_text: str = Field(..., description="Raw ruleset text (PDF → text)")

class RulesetResponse(BaseModel):
    id: str
    name: str
    description: str

@router.post("/create", response_model=RulesetResponse)
def create_ruleset_endpoint(req: RulesetCreateRequest):
    try:
        rs = create_ruleset(req.name, req.description, req.full_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create ruleset: {e}")
    return rs

@router.get("/list", response_model=List[RulesetResponse])
def list_rulesets_endpoint():
    try:
        return list_rulesets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list rulesets: {e}")

@router.get("/{ruleset_id}", response_model=RulesetResponse)
def get_ruleset_endpoint(ruleset_id: str):
    rs = get_ruleset(ruleset_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return {"id": rs["id"], "name": rs["name"], "description": rs["description"]}
