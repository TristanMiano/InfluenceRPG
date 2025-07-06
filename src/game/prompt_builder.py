"""
src/game/prompt_builder.py

Prompt Assembly Logic for RAG-enabled game setup generation.
Builds a polished LLM prompt combining universe information, game description,
and retrieved ruleset chunks.
"""

from src.utils.prompt_loader import load_prompt_template

def assemble_generation_prompt(
    universe_name: str,
    universe_description: str,
    game_description: str,
    chunks: list[str]
) -> str:
    """
    Construct the final prompt for the LLM to generate a richly detailed game setup.

    Args:
        universe_name: Name of the selected universe.
        universe_description: Text describing the universe.
        game_description: User-provided description of the new game.
        chunks: List of background lore excerpts retrieved via RAG.

    Returns:
        A single string prompt, polished and ready for LLM consumption.
    """
    # Intro and context via template
    template = load_prompt_template("game_prompt_builder.txt")
    lore_section = "Background Lore Excerpts (from the ruleset):\n"
    for idx, chunk in enumerate(chunks, start=1):
        lore_section += f"{idx}. {chunk.strip()}\n\n"
    prompt = template.format(
        universe_name=universe_name,
        universe_description=universe_description,
        game_description=game_description,
        lore_section=lore_section,
    )
    return prompt
