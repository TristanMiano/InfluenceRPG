# src/game/conflict_detector.py

import json
from src.db import universe_db
from src.llm.llm_client import generate_completion
from src.game.merger import run_merger_for_conflict

def run_conflict_detector(universe_id: str):
    """
    Scan recent universe events and detect hard conflicts via LLM.
    """
    # 1) Pull the most recent events
    events = universe_db.list_events(universe_id, limit=20)

    # 2) Build an LLM prompt
    prompt_lines = [
        "You are a conflict detector. Given the following universe events,",
        "identify any \"hard conflicts\" that should trigger merging of game instances.",
        "Output a JSON array; each object should have:",
        "  - game_ids: list of instance IDs involved",
        "  - description: brief text describing the conflict",
        "",
        "Events:"
    ]
    # reverse so oldest first
    for e in reversed(events):
        payload = e["event_payload"]
        payload_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
        prompt_lines.append(f"{e['event_time']} [{e['game_id']}] {e['event_type']} – {payload_str}")

    full_prompt = "\n".join(prompt_lines)

    # 3) Call the LLM
    response_text = generate_completion(full_prompt)

    # 4) Parse and record any conflicts
    try:
        conflicts = json.loads(response_text)
    except json.JSONDecodeError:
        # could log this for inspection
        return

    for conflict in conflicts:
        universe_db.record_conflict(universe_id, conflict)
        run_merger_for_conflict(universe_id, conflict)
