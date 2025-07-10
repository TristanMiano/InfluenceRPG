import json
import random
from typing import Any, Dict, List

from src.llm.llm_client import generate_completion
from src.game.rag import retrieve_chunks

DEFAULT_TOP_K = 5


def plan_tool_calls(conversation_context: str, trigger_prompt: str) -> Dict[str, Any]:
    """Determine if any tools should be called before the GM responds.

    The LLM examines the latest conversation context and player prompt to
    see if game mechanics should run. The model must return a JSON object
    describing the desired tool calls. Supported tools:
      - ``dice``: request dice rolls. Example ``{"dice": {"num_rolls": 2, "sides": 20}}``
      - ``lore``: retrieve ruleset lore. Example ``{"lore": {"query": "stealth rules", "top_k": 3}}``
      - ``branch``: split the game into groups. Example ``{"branch": {"groups": [{"character_ids": ["c1"], "description": "Team A"}]}}``
    If no tools are needed, it should return ``{}``.
    """
    tool_prompt = (
        "You decide if the next GM update requires calling game mechanics.\n"
        "Return ONLY a JSON object describing necessary tool calls.\n"
        "Example for dice: {\"dice\": {\"num_rolls\": 1, \"sides\": 20}}\n"
        "Example for lore lookup: {\"lore\": {\"query\": \"movement rules\", \"top_k\": 3}}\n"
        "Example for branching: {\"branch\": {\"groups\": [{\"character_ids\": [\"c1\"], \"description\": \"Team A\"}]}}\n"
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
    
def query_ruleset_chunks(ruleset_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> List[str]:
    """Retrieve relevant ruleset chunks using the RAG module."""
    try:
        return retrieve_chunks(ruleset_id, query, top_k)
    except Exception:
        return []