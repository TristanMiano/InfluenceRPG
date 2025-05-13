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
