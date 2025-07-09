# src/game/conflict_detector.py

import json
from src.db import universe_db
from src.db import game_db
from src.llm.llm_client import generate_completion
from src.game.merger import run_merger_for_conflict
from src.utils.prompt_loader import load_prompt_template

def run_conflict_detector(universe_id: str):
    """
    Scan recent universe events and detect hard conflicts via LLM.
    """
    # 1) Pull the most recent events
    events = universe_db.list_events(universe_id, limit=20)

    # Filter out events from games that are already closed or merged
    filtered_events = []
    status_cache: dict[str, str | None] = {}
    for e in events:
        gid = e.get("game_id")
        if gid not in status_cache:
            try:
                g = game_db.get_game(gid)
                status_cache[gid] = g.get("status") if g else None
            except Exception:
                status_cache[gid] = None

        if status_cache[gid] in ("closed", "merged"):
            continue
        filtered_events.append(e)
    events = filtered_events

    # 2) Build an LLM prompt using template
    template = load_prompt_template("conflict_detector_system.txt")
    prompt_lines = [template]
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

        # Deduplicate any repeated game IDs
        game_ids = conflict.get("game_ids", [])
        conflict["game_ids"] = list(dict.fromkeys(game_ids))

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
