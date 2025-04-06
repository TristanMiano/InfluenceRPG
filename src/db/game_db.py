# src/db/game_db.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4

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
