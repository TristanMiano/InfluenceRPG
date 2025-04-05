# src/db/character_db.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4

def get_db_config() -> dict:
    """Load database configuration from project_root/config/db_config.json."""
    # __file__ is something like '.../rpg_project/src/db/character_db.py'
    # We want to go up three levels to reach the project root.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config", "db_config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection():
    """Establish a connection to the PostgreSQL database using configuration."""
    config = get_db_config()
    conn = psycopg2.connect(
        host=config.get("DB_HOST", "localhost"),
        port=config.get("DB_PORT", 5432),
        dbname=config.get("DB_NAME", "influence_rpg"),
        user=config.get("DB_USER", "postgres"),
        password=config.get("DB_PASSWORD", "postgres")
    )
    return conn

def create_character(owner: str, name: str, character_class: str) -> dict:
    """
    Insert a new character record into the database and return it as a dictionary.
    """
    char_id = str(uuid4())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO characters (id, owner, name, character_class) VALUES (%s, %s, %s, %s)",
                (char_id, owner, name, character_class)
            )
            conn.commit()
            return {"id": char_id, "owner": owner, "name": name, "character_class": character_class}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_characters_by_owner(owner: str) -> list:
    """
    Retrieve all character records for a given owner from the database.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, owner, name, character_class FROM characters WHERE owner = %s", (owner,))
            return cur.fetchall()
    except Exception as e:
        raise e
    finally:
        conn.close()
