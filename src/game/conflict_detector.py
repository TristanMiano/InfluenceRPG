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
        "You are a conflict detector for the online role-playing game InfluenceRPG. Given the following universe events,",
        "identify any \"hard conflicts\" that should trigger merging of game instances.",
        "A \"hard conflict\" is defined as when two game instances occur in overlapping areas,",
        "and therefore the events within each game should be immediately visible to each other,",
        "or affect one another. The purpose of conflict detection is to trigger a merger of these ",
        "game instances into one.", 
        "Key things to look out for: ",
        "-Occur in the same named area or location in time.",
        "-A character in one instance is named as a character in another instance.",
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
    
    # 4) Strip markdown/code fences if present
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # remove first fence line
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # remove last fence line
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    
    #Debug logging
    #print("=== Conflict Prompt ===\n", full_prompt)
    #print("=== LLM Response ===\n", cleaned)

    # 4) Parse and record any conflicts
    try:
        conflicts = json.loads(cleaned)
    except json.JSONDecodeError:
        # could log this for inspection
        print("[conflict_detector] ❌ JSON decode failed:", response_text)
        return

    for conflict in conflicts:
        # ---- DEBUG START ----
        print(f"[conflict_detector] 🔍 Detected conflict: {conflict}")
        try:
            universe_db.record_conflict(universe_id, conflict)
            print(f"[conflict_detector] ✅ Recorded conflict to DB for universe {universe_id}")
        except Exception as e:
            print(f"[conflict_detector] ❌ record_conflict failed:", e)
        try:
            run_merger_for_conflict(universe_id, conflict)
            print(f"[conflict_detector] 🚀 Merger run for conflict in universe {universe_id}")
        except Exception as e:
            print(f"[conflict_detector] ❌ run_merger_for_conflict failed:", e)
        # ---- DEBUG END ----
