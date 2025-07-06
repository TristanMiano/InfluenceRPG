from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import re

from src.db.ruleset_db import get_ruleset
from src.llm.llm_client import generate_completion
from src.utils.prompt_loader import load_prompt_template

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

    # 2) Build system prompt from template
    template = load_prompt_template("character_wizard_system.txt")
    system_prompt = template.format(ruleset_text=ruleset_text)

    # 3) Append history
    history_prompt = ""
    for qa in req.history:
        history_prompt += f"Q: {qa.question}\nA: {qa.answer}\n\n"

    # 4) Instruction for next step
    if not req.history:
        next_step_prompt = "Begin by asking for the character's name."
    else:
        next_step_prompt = "Based on the above, ask the next question. If there are no further questions, output only the final JSON object."

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
        
    m = re.search(r'(\{[\s\S]*\})', cleaned)
    if m:
        # Found JSON → discard everything else
        cleaned = m.group(1).strip()
    else:
        # 2) Otherwise, strip off any “A:” and what follows
        if cleaned.startswith("Q:") and "A:" in cleaned:
            cleaned = cleaned.split("A:")[0].strip()
    
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
