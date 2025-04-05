#!/usr/bin/env python3
"""
create_account.py - Script to create a new user account in the database.

Usage:
    python -m src.auth.create_account <username> <password> [role]

If role is not provided, it defaults to "player".
"""

import sys
import os

# Compute the project root (three levels up from the current file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import psycopg2
from src.utils.security import hash_password

def get_db_config() -> dict:
    """
    Load database configuration from project_root/config/db_config.json.
    """
    config_path = os.path.join(project_root, "config", "db_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading DB config from {config_path}: {e}")
        return {}

def get_db_connection():
    """
    Establish a connection to the PostgreSQL database using the configuration.
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

def create_account(username: str, password: str, role: str = "player"):
    """
    Creates a new user account in the users table if the username does not already exist.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if the username already exists.
            cur.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                print(f"User '{username}' already exists.")
                return
            # Insert the new user into the database.
            cur.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
                (username, hash_password(password), role)
            )
            conn.commit()
            print(f"User '{username}' created successfully.")
    except Exception as e:
        conn.rollback()
        print("Error creating account:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m src.auth.create_account <username> <password> [role]")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "player"
    
    create_account(username, password, role)
