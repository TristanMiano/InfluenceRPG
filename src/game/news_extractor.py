# src/game/news_extractor.py

import json
from src.db import universe_db
from src.llm.llm_client import generate_completion
from src.utils.prompt_loader import load_prompt_template

def run_news_extractor(universe_id: str, event_limit: int = 50) -> str:
    """
    Extract news for a universe by summarizing recent events.
    Returns the generated summary.
    """
    # 1) Pull recent events
    events = universe_db.list_events(universe_id, limit=event_limit)
    
    # → if there are no events at all, nothing to do
    if not events:
        return ""

    # 2) Have we already summarized up through the newest event?
    #    Compare the max event_time vs. last published_at in universe_news
    latest_event = max(e["event_time"] for e in events)
    last_news = universe_db.list_news(universe_id, limit=1)
    if last_news:
        last_published = last_news[0]["published_at"]
        if latest_event <= last_published:
            # no new events since our last bulletin
            print(f"[news_extractor] No new events since {last_published}, skipping.")
            return ""

    # 3) Build an LLM prompt using template
    template = load_prompt_template("news_extractor_system.txt")
    prompt_lines = [template]
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
