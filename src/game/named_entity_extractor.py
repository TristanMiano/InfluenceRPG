"""Named Entity Extractor

This module calls an LLM to extract named entities from game chat history.
It outputs structured JSON based on the schema defined in entity_schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.llm.llm_client import generate_completion
from src.utils.prompt_loader import load_prompt_template

# Path to the JSON schema describing the response
SCHEMA_PATH = Path(__file__).resolve().parent / "entity_schema.json"


def run_named_entity_extractor(conversation: str) -> Dict[str, Any]:
    """Run the LLM based extractor on a conversation transcript.

    Parameters
    ----------
    conversation: str
        The chat history to analyze.

    Returns
    -------
    dict
        Parsed JSON object of extracted entities. An empty dict is returned on
        failure.
    """
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    template = load_prompt_template("entity_extractor_system.txt")
    prompt = template.format(schema=schema_text, conversation=conversation)

    response_text = generate_completion(prompt)

    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print("[named_entity_extractor] JSON decode failed")
        return {}

    return data
