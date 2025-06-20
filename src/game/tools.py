import json
import random
from typing import Any, Dict, List

from src.llm.llm_client import generate_completion


def plan_tool_calls(conversation_context: str, trigger_prompt: str) -> Dict[str, Any]:
    """Determine if any tools should be called before the GM responds.

    This uses the LLM to inspect the conversation and the latest player trigger
    to see if actions like dice rolls are required. The LLM must respond with a
    JSON object describing the tools to invoke. Example:
        {"dice": {"num_rolls": 2, "sides": 20}}
    If no tools are needed, it should return an empty JSON object.
    """
    tool_prompt = (
        "You decide if the next GM update requires calling game mechanics.\n"
        "Return ONLY a JSON object describing necessary tool calls.\n"
        "Example for one twenty-sided roll: {\"dice\": {\"num_rolls\": 1, \"sides\": 20}}\n"
        "If nothing is required, return {}.\n\n"
        f"Conversation History:\n{conversation_context}\n\n"
        f"Latest Prompt: {trigger_prompt}\n\n"
        "Tool Calls:"
    )
    raw = generate_completion(prompt=tool_prompt, conversation_context="")
    try:
        return json.loads(raw.strip())
    except Exception:
        return {}


def roll_dice(num_rolls: int, sides: int = 20) -> List[int]:
    """Roll a die of the specified number of sides multiple times."""
    return [random.randint(1, sides) for _ in range(max(1, num_rolls))]