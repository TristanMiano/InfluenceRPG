from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.db.universe_db import get_universe, list_news
from src.game.rag import retrieve_chunks
from src.game.prompt_builder import assemble_generation_prompt
from src.llm.llm_client import generate_completion

router = APIRouter()

class GenerateSetupRequest(BaseModel):
    universe_id: str = Field(..., description="UUID of the selected universe")
    game_description: str = Field(..., description="User-provided description of the new game")

class GenerateSetupResponse(BaseModel):
    generated_setup: str

@router.post("/api/game/generate-setup", response_model=GenerateSetupResponse, tags=["game"])
def generate_setup_endpoint(req: GenerateSetupRequest):
    # 1) Fetch universe metadata
    uni = get_universe(req.universe_id)
    if not uni:
        raise HTTPException(status_code=404, detail="Universe not found")

    # 2) Ensure the universe has a linked ruleset
    ruleset_id = uni.get("ruleset_id")
    if not ruleset_id:
        raise HTTPException(status_code=400, detail="Universe has no ruleset assigned")

    # 3) Retrieve top-K lore chunks via RAG
    #    Combine universe context and game description for the query
    query = f"{uni['name']}: {uni['description']} -- New Game: {req.game_description}"
    chunks = retrieve_chunks(ruleset_id, query)

    # 4) Fetch recent news (limit 5)
    news_items = list_news(req.universe_id, limit=5)
    # 5) Assemble the generation prompt
    prompt = assemble_generation_prompt(
        universe_name=uni['name'],
        universe_description=uni['description'],
        game_description=req.game_description,
        chunks=chunks,
        news_items=news_items,
    )

    generated = generate_completion(prompt)

    return GenerateSetupResponse(generated_setup=generated)
