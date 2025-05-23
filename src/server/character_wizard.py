from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json

from src.db.ruleset_db import get_ruleset
from src.llm.llm_client import generate_completion

router = APIRouter(prefix="/api/character", tags=["character"])

class WizardQA(BaseModel):
    question: str
    answer: str

class WizardRequest(BaseModel):
    ruleset_id: str
    history: List[WizardQA] = Field(
        default_factory=list,
        description="Prior question/answer pairs"
    )

class WizardResponse(BaseModel):
    question: Optional[str] = None
    complete: bool
    name: Optional[str] = None
    character_data: Optional[Dict[str, Any]] = None

@router.post("/wizard", response_model=WizardResponse)
def character_wizard(req: WizardRequest):
    # 1) Load ruleset text
    rs = get_ruleset(req.ruleset_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    ruleset_text = rs["char_creation"]

    # 2) Build system prompt
    system_prompt = (
        "You are a character-creation assistant. Your job is to ask the user one question "
        "at a time to gather all information required by the following ruleset. "
        "When all required fields have been collected, output **only** the final JSON object with "
        "– name: the character’s name string "
        "– all other fields under character_data as a sub-object.\n\n"
        f"--- RULESET BEGIN ---\n{ruleset_text}\n--- RULESET END ---\n\n"
    )

    # 3) Append history
    history_prompt = ""
    for qa in req.history:
        history_prompt += f"Q: {qa.question}\nA: {qa.answer}\n\n"

    # 4) Instruction for next step
    if not req.history:
        next_step_prompt = "Begin by asking for the character's name."
    else:
        next_step_prompt = "Based on the above, ask the next question."

    full_prompt = system_prompt + history_prompt + next_step_prompt
    
    print("Prompt:")
    print(full_prompt)

    # 5) Call the LLM
    response_text = generate_completion(full_prompt).strip()
    
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # remove first fence line
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # remove last fence line
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    
    print("Response:")
    print(cleaned)

    # 6) If the LLM returned JSON, treat as completion
    try:
        data = json.loads(cleaned)
        name = data.pop("name", None)
        return WizardResponse(
            question=None,
            complete=True,
            name=name,
            character_data=data
        )
    except json.JSONDecodeError:
        # Otherwise, it's a question to ask the user
        return WizardResponse(question=cleaned, complete=False)
