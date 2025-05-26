"""
src/game/prompt_builder.py

Prompt Assembly Logic for RAG-enabled game setup generation.
Builds a polished LLM prompt combining universe information, game description,
and retrieved ruleset chunks.
"""

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
    # Intro and context
    intro = (
        "You are a game-creation assistant.\n"
        "Using the information below, produce an immersive, detailed game setup:\n\n"
        f"Universe: {universe_name}\n"
        f"Universe Description: {universe_description}\n\n"
        f"Game Description: {game_description}\n\n"
    )

    # Background lore excerpts
    lore_section = "Background Lore Excerpts (from the ruleset):\n"
    for idx, chunk in enumerate(chunks, start=1):
        lore_section += f"{idx}. {chunk.strip()}\n\n"

    # Clear instructions
    instruction = (
        "The Background Lore Excerpts above were retrieved using cosine similarity between text "
        "embeddings of the excerpts and a query made from the Universe and Game Descriptions. "
        "Expand and elaborate on the game setup, adhering closely to the Game Description above. "
        "Integrate relevant details from the Background Lore Excerpts and respect any stipulations "
        "or restrictions in the Universe Description. Be creative and ensure the final narrative "
        "is cohesive, engaging, and faithful to the ruleset's lore."
    )

    # Assemble full prompt
    prompt = intro + lore_section + instruction
    return prompt
