from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import re

from src.db.ruleset_db import get_ruleset
from src.llm.llm_client import generate_completion
from src.utils.prompt_loader import load_prompt_template
from src.game.tools import roll_dice

def _extract_tools(text: str) -> (str, Dict[str, Any]):
    """Return plain text and any requested tool calls."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    m = re.search(r'(\{[\s\S]*\})', cleaned)
    json_str = m.group(1).strip() if m else cleaned
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and "tool_calls" in data:
            tools = data.get("tool_calls") or {}
            if not isinstance(tools, dict):
                tools = {}
            text_out = data.get("narrative", "")
            return text_out, tools
    except Exception:
        pass
    return cleaned, {}

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

    extra_context = ""
    while True:
        full_prompt = system_prompt + history_prompt + extra_context + next_step_prompt

        print("Prompt:")
        print(full_prompt)

        response_text = generate_completion(full_prompt).strip()
        text, tools = _extract_tools(response_text)

        if tools.get("dice"):
            spec = tools["dice"] or {}
            num = int(spec.get("num_rolls", 1))
            sides = int(spec.get("sides", 20))
            results = roll_dice(num, sides)
            extra_context += f"Dice results for {num}d{sides}: {results}\n\n"
            continue

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        m = re.search(r'(\{[\s\S]*\})', cleaned)
        if m:
            cleaned = m.group(1).strip()
        else:
            if cleaned.startswith("Q:") and "A:" in cleaned:
                cleaned = cleaned.split("A:")[0].strip()

        print("Response:")
        print(cleaned)

        try:
            data = json.loads(cleaned)
            name = data.pop("name", None)
            char_data = data.get("character_data", data)
            return WizardResponse(
                question=None,
                complete=True,
                name=name,
                character_data=char_data
            )
        except json.JSONDecodeError:
            return WizardResponse(question=cleaned, complete=False)
