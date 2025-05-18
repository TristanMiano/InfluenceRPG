# src/db/character_db.py

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4
from pathlib import Path

def get_db_config() -> dict:
    """Load database configuration from project_root/config/db_config.json."""
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config" / "db_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection():
    """Establish a connection to the PostgreSQL database using configuration."""
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg.get("DB_HOST", "localhost"),
        port=cfg.get("DB_PORT", 5432),
        dbname=cfg.get("DB_NAME", "influence_rpg"),
        user=cfg.get("DB_USER", "postgres"),
        password=cfg.get("DB_PASSWORD", "postgres")
    )

def create_character(owner: str, universe_id: str, name: str, character_data: dict) -> dict:
    """
    Insert a new character tied to a universe.
    """
    char_id = str(uuid4())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO characters
                  (id, owner, universe_id, name, character_data)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (char_id, owner, universe_id, name, json.dumps(character_data))
            )
            conn.commit()
        return {
            "id": char_id,
            "owner": owner,
            "universe_id": universe_id,
            "name": name,
            "character_data": character_data
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 2. New helper to check for existing
def get_character_by_owner_and_universe(owner: str, universe_id: str) -> dict | None:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, owner, universe_id, name, character_data
                  FROM characters
                 WHERE owner = %s AND universe_id = %s
                """,
                (owner, universe_id)
            )
            return cur.fetchone()
    finally:
        conn.close()

def get_characters_by_owner(owner: str) -> list[dict]:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, owner, universe_id, name, character_data
                  FROM characters
                 WHERE owner = %s
                """,
                (owner,)
            )
            return cur.fetchall()
    finally:
        conn.close()

def get_character_by_id(char_id: str) -> dict | None:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, owner, universe_id, name, character_data
                  FROM characters
                 WHERE id = %s
                """,
                (char_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()
