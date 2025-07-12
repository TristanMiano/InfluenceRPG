# src/game/brancher.py

import json
from src.db import universe_db
from src.db.game_db import (
    create_game,
    join_game,
    update_game_status,
    get_game,
    save_chat_message,
    get_latest_game_summary,
)
from src.server.notifications import notify_branch


def run_branch(original_game_id: str, groups: list[dict], *, send_notifications: bool = True) -> list[dict]:
    """Split a single game into multiple new ones based on character groups.

    Each group should be a dict with ``character_ids`` (list[str]) and
    ``description`` fields. Returns a list of dictionaries containing the
    new game object and its assigned character IDs.
    """
    base = get_game(original_game_id)
    base_name = base["name"] if base else original_game_id

    new_games: list[dict] = []

    summary_text = get_latest_game_summary(original_game_id)
    uni_ids = universe_db.list_universes_for_game(original_game_id)

    for grp in groups:
        desc = grp.get("description", "").strip()
        new_name = f"Branch of {base_name}: {desc}" if desc else f"Branch of {base_name}"
        g = create_game(new_name)
        new_id = g["id"]

        for uid in uni_ids:
            universe_db.add_game_to_universe(uid, new_id)

        for cid in grp.get("character_ids", []):
            try:
                join_game(new_id, cid)
            except Exception:
                pass

        if summary_text:
            prefix = f"Summary of {base_name}:\n{summary_text}"
            save_chat_message(new_id, "System", prefix)

        new_games.append({"game": g, "character_ids": grp.get("character_ids", [])})

    update_game_status(original_game_id, "branched")

    new_ids = [ng["game"]["id"] for ng in new_games]
    branch_info = {"groups": groups}
    universe_db.record_branch(original_game_id, new_ids, branch_info)
    for uid in uni_ids:
        universe_db.record_event(
            universe_id=uid,
            game_id=original_game_id,
            event_type="branch",
            payload={"new_game_ids": new_ids, "groups": groups},
        )
        for ng in new_games:
            universe_db.record_event(
                universe_id=uid,
                game_id=ng["game"]["id"],
                event_type="branched_from",
                payload={"original_game_id": original_game_id},
            )

    if send_notifications:
        notify_branch(original_game_id, new_games)

    return new_games
