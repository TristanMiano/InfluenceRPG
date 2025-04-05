# src/auth/auth.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from src.utils.security import hash_password, verify_password

def get_db_config() -> dict:
    """
    Load database configuration from config/db_config.json.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust path: go up two levels to project root, then into config
    config_path = os.path.join(base_dir, "..", "..", "config", "db_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading DB config from {config_path}: {e}")
        return {}

def get_db_connection():
    """
    Establish a new connection to the PostgreSQL database using the configuration.
    """
    config = get_db_config()
    try:
        conn = psycopg2.connect(
            host=config.get("DB_HOST", "localhost"),
            port=config.get("DB_PORT", 5432),
            dbname=config.get("DB_NAME", "influence_rpg"),
            user=config.get("DB_USER", "postgres"),
            password=config.get("DB_PASSWORD", "postgres")
        )
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        raise

def authenticate_user(username: str, password: str):
    """
    Authenticate the user by retrieving their data from the database and verifying the password.
    
    Returns:
        A dictionary containing user details if credentials are valid; otherwise, None.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT username, hashed_password, role FROM users WHERE username = %s",
                (username,)
            )
            user = cur.fetchone()
            if not user:
                return None
            if not verify_password(password, user["hashed_password"]):
                return None
            return user
    except Exception as e:
        print("Error during authentication:", e)
        return None
    finally:
        conn.close()