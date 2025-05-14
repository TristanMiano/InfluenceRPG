# src/game/initial_prompt.py

import os
from pathlib import Path
from typing import List, Optional

from src.llm.llm_client import generate_completion

# Directory where current game rule documents are stored
RULES_DIR = Path(__file__).parent.parent / "design"


def load_rule_files(
    rules_dir: Path = RULES_DIR,
    extensions: List[str] = [".md", ".txt"]
) -> List[str]:
    """
    Load text content from rule definition files in the design directory.
    """
    contents = []
    for path in rules_dir.rglob("*"):
        if path.suffix.lower() in extensions:
            try:
                contents.append(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return contents


def compact_rules(
    rule_texts: List[str],
    max_chars: int = 5000
) -> str:
    """
    Combine and truncate rule texts to fit within a character limit.
    """
    combined = "\n\n".join(rule_texts)
    if len(combined) > max_chars:
        return combined[:max_chars] + "\n\n[...truncated]"
    return combined


def create_initial_prompt(
    initial_details: str,
    game_name: str,
    universe_name: Optional[str],
    universe_description: Optional[str],
    starting_player: str,
    rules_dir: Path = RULES_DIR
) -> str:
    """
    Construct the initial prompt for the Game Master LLM on game creation,
    including game metadata, universe info, rules, and setup details.
    """
    # Load and compact rules
    rule_texts = load_rule_files(rules_dir)
    rules_summary = compact_rules(rule_texts)

    # Build metadata header
    meta_lines = [
        f"Game Name: {game_name}",
        f"Universe: {universe_name or 'None'}",
        f"Universe Description: {universe_description or 'None'}",
        f"Starting Player: {starting_player}",
        ""
    ]

    prompt = (
        "You are the Game Master AI for the Influence RPG.\n"
        + "\n".join(meta_lines)
        + "\nBelow is the current game rule set (subject to updates during development):\n\n"
        f"{rules_summary}\n\n"
        "The human GM has provided these setup details for this new game:\n\n"
        f"{initial_details}\n\n"
        "Based on the metadata, rules, and the setup, generate an initial narrative scene to start the adventure."
    )
    return prompt


def generate_initial_scene(
    initial_details: str,
    game_name: str,
    universe_name: Optional[str],
    universe_description: Optional[str],
    starting_player: str
) -> str:
    """
    Generate the first narrative scene by calling the LLM with the constructed prompt.
    """
    prompt = create_initial_prompt(
        initial_details,
        game_name,
        universe_name,
        universe_description,
        starting_player
    )
    return generate_completion(prompt)
