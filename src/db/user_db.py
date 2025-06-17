# src/db/user_db.py

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

from src.utils.security import hash_password, verify_password


def get_db_config() -> dict:
    """Load database configuration from project root config/db_config.json."""
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config" / "db_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg.get("DB_HOST", "localhost"),
        port=cfg.get("DB_PORT", 5432),
        dbname=cfg.get("DB_NAME", "influence_rpg"),
        user=cfg.get("DB_USER", "postgres"),
        password=cfg.get("DB_PASSWORD", "postgres"),
    )


def verify_user_password(username: str, password: str) -> bool:
    """Return True if the password matches the stored hash for username."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT hashed_password FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            if not row:
                return False
            return verify_password(password, row["hashed_password"])
    finally:
        conn.close()


def update_password(username: str, new_password: str) -> None:
    """Update the user's password hash."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET hashed_password = %s WHERE username = %s",
                (hash_password(new_password), username),
            )
            conn.commit()
    finally:
        conn.close()