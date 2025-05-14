# src/game/merger.py

import json
from src.db import universe_db
from src.db.game_db import (
    create_game,
    join_game,
    list_players_in_game,
    update_game_status,
    get_game
)

def run_merger_for_conflict(universe_id: str, conflict_info: dict):
    """
    Merge the game instances in conflict_info['game_ids'] into a new single game.
    """
    from_ids = conflict_info.get("game_ids", [])
    if len(from_ids) < 2:
        # nothing to merge
        return

    # 1) Build a merged game name from the existing ones
    existing_names = [ get_game(gid)["name"] for gid in from_ids ]
    new_name = "Merged: " + " + ".join(existing_names)

    # 2) Create the new merged game instance
    new_game = create_game(new_name)
    new_game_id = new_game["id"]

    # 3) Link the new game into the universe
    universe_db.add_game_to_universe(universe_id, new_game_id)

    # 4) Carry over all players from the old games
    for old_id in from_ids:
        players = list_players_in_game(old_id)
        for char_id in players:
            try:
                join_game(new_game_id, char_id)
            except Exception:
                # ignore duplicates or errors
                pass
        # 5) Mark the old game as merged
        update_game_status(old_id, "merged")

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
