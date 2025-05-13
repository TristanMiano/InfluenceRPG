# src/game/merger.py

import json
from src.db import universe_db
from src.db.game_db import create_game, list_players_in_game, update_game_status
from uuid import uuid4

def run_merger_for_conflict(universe_id: str, conflict_info: dict):
    """
    Merge the game instances in conflict_info['game_ids'] into a new single game.
    """
    from_ids = conflict_info.get("game_ids", [])
    # Build a merged game name from existing names
    existing_names = [create_game  # placeholder, will fix below
    ]

    # Fetch each game's name
    existing_names = [game_db.get_game(gid)["name"] for gid in from_ids]
    new_name = "Merged: " + " + ".join(existing_names)

    # 1) Create the new merged game instance
    new_game = create_game(new_name)
    new_game_id = new_game["id"]

    # 2) Link the new game to this universe
    universe_db.add_game_to_universe(universe_id, new_game_id)

    # 3) Carry over all players from the old games
    for old_id in from_ids:
        player_ids = list_players_in_game(old_id)
        for char_id in player_ids:
            try:
                create_game.join_game(new_game_id, char_id)
            except Exception:
                # ignore if already joined
                continue
        # 4) Mark the old game as merged
        update_game_status(old_id, "merged")

    # 5) Record the merger event in the universe
    #   a) In the mergers log
    universe_db.record_merger(universe_id, from_ids, new_game_id)

    #   b) As a universe event
    universe_db.record_event(
        universe_id=universe_id,
        game_id=new_game_id,
        event_type="merger",
        event_payload={
            "from_instance_ids": from_ids,
            "into_instance_id": new_game_id
        }
    )
