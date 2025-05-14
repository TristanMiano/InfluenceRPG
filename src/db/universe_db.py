# src/db/universe_db.py

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4
from pathlib import Path

def get_db_config() -> dict:
    """Load DB config from config/db_config.json in project root."""
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config" / "db_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection():
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg.get("DB_HOST", "localhost"),
        port=cfg.get("DB_PORT", 5432),
        dbname=cfg.get("DB_NAME", "influence_rpg"),
        user=cfg.get("DB_USER", "postgres"),
        password=cfg.get("DB_PASSWORD", "postgres")
    )

def create_universe(name: str, description: str = "") -> dict:
    """Insert a new universe record."""
    uni_id = str(uuid4())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO universes (id, name, description) VALUES (%s, %s, %s)",
                (uni_id, name, description)
            )
            conn.commit()
        return {"id": uni_id, "name": name, "description": description}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_universes() -> list[dict]:
    """Return all universes."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, description, created_at FROM universes ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()

def add_game_to_universe(universe_id: str, game_id: str):
    """Link an existing game into a universe."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO universe_games (universe_id, game_id) VALUES (%s, %s)",
                (universe_id, game_id)
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_universes_for_game(game_id: str) -> list[str]:
    """
    Return a list of universe IDs this game is joined to.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT universe_id FROM universe_games WHERE game_id = %s",
                (game_id,)
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def record_event(universe_id: str, game_id: str, event_type: str, event_payload: dict):
    """
    Insert a new event into the universe_events table.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO universe_events
                  (universe_id, game_id, event_type, event_payload)
                VALUES (%s, %s, %s, %s)
                """,
                (universe_id, game_id, event_type, json.dumps(event_payload))
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_events(universe_id: str, limit: int = 50) -> list[dict]:
    """
    Retrieve recent events for a universe.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, game_id, event_type, event_payload, event_time "
                "FROM universe_events "
                "WHERE universe_id = %s "
                "ORDER BY event_time DESC "
                "LIMIT %s",
                (universe_id, limit)
            )
            return cur.fetchall()
    finally:
        conn.close()

def record_conflict(universe_id: str, conflict_info: dict):
    """
    Insert a detected conflict into conflict_detections.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conflict_detections (universe_id, conflict_info) VALUES (%s, %s)",
                (universe_id, json.dumps(conflict_info))
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def record_merger(universe_id: str, from_instance_ids: list[str], into_instance_id: str):
    """
    Insert a merger record into the mergers table.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mergers (universe_id, from_instance_ids, into_instance_id) "
                "VALUES (%s, %s, %s)",
                (universe_id, json.dumps(from_instance_ids), into_instance_id)
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_news(universe_id: str, limit: int = 20) -> list[dict]:
    """
    Retrieve recent news items for a universe.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, summary, published_at FROM universe_news "
                "WHERE universe_id = %s "
                "ORDER BY published_at DESC "
                "LIMIT %s",
                (universe_id, limit)
            )
            return cur.fetchall()
    finally:
        conn.close()

def record_news(universe_id: str, summary: str):
    """
    Insert a news summary into universe_news.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO universe_news (universe_id, summary) VALUES (%s, %s)",
                (universe_id, summary)
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        
def list_conflicts(universe_id: str, limit: int = 20) -> list[dict]:
    """
    Retrieve recent detected conflicts for a universe.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, conflict_info, detected_at "
                "FROM conflict_detections "
                "WHERE universe_id = %s "
                "ORDER BY detected_at DESC "
                "LIMIT %s",
                (universe_id, limit)
            )
            return [
                {"id": row["id"], 
                 "conflict_info": row["conflict_info"], 
                 "detected_at": row["detected_at"]}
                for row in cur.fetchall()
            ]
    finally:
        conn.close()

def get_universe(universe_id: str) -> dict | None:
    """
    Retrieve a universe record (id, name, description) by its ID.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, description, created_at FROM universes WHERE id = %s",
                (universe_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()
