# src/game/merger.py

import json
from src.db import universe_db
from src.db.game_db import (
    create_game,
    join_game,
    list_players_in_game,
    update_game_status,
    get_game,
    save_chat_message,
    get_latest_game_summary,
)

def run_merger_for_conflict(universe_id: str, conflict_info: dict):
    """
    Merge the game instances in conflict_info['game_ids'] into a new single game.
    """
    from_ids = conflict_info.get("game_ids", [])

    # Deduplicate IDs to avoid merging a game with itself
    from_ids = list(dict.fromkeys(from_ids))

    if len(from_ids) < 2:
        # nothing to merge after removing duplicates
        return

    # 1) Build a merged game name from the existing ones
    existing_names = [ get_game(gid)["name"] for gid in from_ids ]
    new_name = "Merged: " + " + ".join(existing_names)

    # 2) Create the new merged game instance
    new_game = create_game(new_name)
    new_game_id = new_game["id"]

    # 3) Link the new game into the universe
    universe_db.add_game_to_universe(universe_id, new_game_id)

    summaries = []

    # 4) Carry over all players from the old games
    for old_id in from_ids:
        players = list_players_in_game(old_id)
        for char_id in players:
            try:
                join_game(new_game_id, char_id)
            except Exception:
                # ignore duplicates or errors
                pass

        # Collect latest summary if available
        summary_text = get_latest_game_summary(old_id)
        if summary_text:
            old_name = get_game(old_id)["name"]
            summaries.append(f"Summary of {old_name}:\n{summary_text}")

        # 5) Mark the old game as merged
        update_game_status(old_id, "merged")

    # If we gathered summaries, prepend them as a system message
    if summaries:
        combined = "\n\n".join(summaries)
        save_chat_message(new_game_id, "System", combined)

    # 6) Record the merger in the universe layer
    #   a) in the mergers table
    universe_db.record_merger(universe_id, from_ids, new_game_id)
    #   b) as a universe event
    universe_db.record_event(
        universe_id=universe_id,
        game_id=new_game_id,
        event_type="merger",
        event_payload={
            "from_instance_ids": from_ids,
            "into_instance_id": new_game_id
        }
    )
