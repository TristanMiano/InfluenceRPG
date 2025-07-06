# src/db/game_db.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4
from typing import Optional

def get_db_config() -> dict:
    """
    Load database configuration from project_root/config/db_config.json.
    """
    # Go up three levels from the current file to get the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config", "db_config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection():
    """
    Establish a connection to the PostgreSQL database using configuration.
    """
    config = get_db_config()
    conn = psycopg2.connect(
        host=config.get("DB_HOST", "localhost"),
        port=config.get("DB_PORT", 5432),
        dbname=config.get("DB_NAME", "influence_rpg"),
        user=config.get("DB_USER", "postgres"),
        password=config.get("DB_PASSWORD", "postgres")
    )
    return conn

def create_game(name: str) -> dict:
    """
    Create a new game record in the games table.
    Returns a dictionary with the game details.
    """
    game_id = str(uuid4())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO games (id, name, status) VALUES (%s, %s, %s)",
                (game_id, name, "waiting")
            )
            conn.commit()
            return {"id": game_id, "name": name, "status": "waiting"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def list_games() -> list:
    """
    Retrieve all game records.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, status, created_at FROM games")
            return cur.fetchall()
    finally:
        conn.close()

def get_game(game_id: str) -> dict:
    """
    Retrieve a game record by its ID.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, status, created_at FROM games WHERE id = %s", (game_id,))
            return cur.fetchone()
    finally:
        conn.close()

def join_game(game_id: str, character_id: str):
    """
    Insert a record into game_players to indicate a character joining a game.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_players (game_id, character_id) VALUES (%s, %s)",
                (game_id, character_id)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def save_chat_message(game_id: str, sender: str, message: str):
    """
    Insert a chat message into the chat_messages table.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_messages (game_id, sender, message) VALUES (%s, %s, %s)",
                (game_id, sender, message)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def list_chat_messages(game_id: str) -> list:
    """
    Retrieve all chat messages for a given game, ordered by timestamp.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, game_id, sender, message, timestamp FROM chat_messages WHERE game_id = %s ORDER BY timestamp",
                (game_id,)
            )
            return cur.fetchall()
    finally:
        conn.close()

def get_character_for_user_in_game(game_id: str, owner: str) -> Optional[str]:
    """
    Return the character_id for the given owner if they have already joined this game.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT gp.character_id FROM game_players gp "
                "JOIN characters c ON gp.character_id = c.id "
                "WHERE gp.game_id = %s AND c.owner = %s",
                (game_id, owner)
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()

def is_character_in_active_game(character_id: str) -> bool:
    """
    Check if a character is already in a non-finished game (status waiting/active).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM game_players gp "
                "JOIN games g ON gp.game_id = g.id "
                "WHERE gp.character_id = %s AND g.status IN ('waiting','active') LIMIT 1",
                (character_id,)
            )
            return cur.fetchone() is not None
    finally:
        conn.close()

def list_players_in_game(game_id: str) -> list[str]:
    """
    Return a list of character IDs currently joined to the given game.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT character_id FROM game_players WHERE game_id = %s",
                (game_id,)
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def update_game_status(game_id: str, status: str):
    """
    Update the status of a game (e.g. to 'merged').
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE games SET status = %s WHERE id = %s",
                (status, game_id)
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_latest_game_summary(game_id: str) -> Optional[str]:
    """Return the latest summary text for the given game, if any."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT summary FROM game_history "
                "WHERE game_id = %s ORDER BY summary_date DESC LIMIT 1",
                (game_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()
