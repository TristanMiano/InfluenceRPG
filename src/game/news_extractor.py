# src/game/news_extractor.py

import json
from src.db import universe_db
from src.llm.llm_client import generate_completion

def run_news_extractor(universe_id: str, event_limit: int = 50) -> str:
    """
    Extract news for a universe by summarizing recent events.
    Returns the generated summary.
    """
    # 1) Pull recent events
    events = universe_db.list_events(universe_id, limit=event_limit)

    # 2) Build an LLM prompt
    prompt_lines = [
        "You are a news reporter in a shared gaming universe.",
        "Write a concise news bulletin summarizing these recent events:",
        ""
    ]
    # oldest first
    for e in reversed(events):
        payload = e["event_payload"]
        payload_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
        prompt_lines.append(f"{e['event_time']} [{e['game_id']}] {e['event_type']}: {payload_str}")

    full_prompt = "\n".join(prompt_lines)

    # 3) Generate the summary via LLM
    summary = generate_completion(full_prompt)

    # 4) Record the bulletin in the DB
    universe_db.record_news(universe_id, summary)

    return summary
