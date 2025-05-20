# src/game/initial_prompt.py

import os
from pathlib import Path
from typing import List, Optional

from src.llm.llm_client import generate_completion
from src.db.ruleset_db import get_ruleset, get_summary, set_summary

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
    ruleset_id: Optional[str],          # ← new param
    rules_dir: Path = RULES_DIR
) -> str:
    """
    Construct the initial prompt, now including a pre-cached ruleset summary.
    """
    # 1) Load the pre-made summary (or generate & cache it once)
    ruleset_section = ""
    if ruleset_id:
        rs = get_ruleset(ruleset_id)
        if rs:
            summary = get_summary(ruleset_id)
            if not summary:
                # generate a concise summary (max ~2000 chars) and cache it
                snippet = rs["full_text"][:20000]  # first 20k chars
                summary_prompt = (
                    "You are an expert game designer. "
                    "Summarize the following ruleset into a concise overview (≤2000 characters):\n\n"
                    + snippet
                )
                summary = generate_completion(summary_prompt)
                set_summary(ruleset_id, summary)
            ruleset_section = (
                f"Ruleset: {rs['name']} — {rs['description']}\n\n"
                f"{summary}\n\n"
            )

    # 2) Existing rule-file loading (unchanged)
    rule_texts = load_rule_files(rules_dir)
    rules_summary = compact_rules(rule_texts)

    # 3) Build metadata header
    meta_lines = [
        f"Game Name: {game_name}",
        f"Universe: {universe_name or 'None'}",
        f"Universe Description: {universe_description or 'None'}",
        f"Starting Player: {starting_player}",
        ""
    ]

    # 4) Assemble the prompt, with the ruleset_section first
    prompt = (
        "You are the Game Master AI for the Influence RPG.\n\n"
        + ruleset_section
        + "Below is the current game rule set (subject to updates during development):\n\n"
        + rules_summary
        + "\n\n"
        "The human GM has provided these setup details for this new game:\n\n"
        f"{initial_details}\n\n"
        "Based on the metadata, rules, and the setup, generate an initial narrative scene to start the adventure."
    )
    return prompt

# And update generate_initial_scene to accept ruleset_id:
def generate_initial_scene(
    initial_details: str,
    game_name: str,
    universe_name: Optional[str],
    universe_description: Optional[str],
    starting_player: str,
    ruleset_id: Optional[str]      # ← new
) -> str:
    """
    Generate the first narrative scene, injecting the ruleset summary.
    """
    prompt = create_initial_prompt(
        initial_details,
        game_name,
        universe_name,
        universe_description,
        starting_player,
        ruleset_id
    )
    return generate_completion(prompt)
