#!/usr/bin/env python3
"""
db_admin.py

Utility script to manage the Influence RPG database.

Usage:
  python -m src.utils.db_admin rebuild      # Drop and recreate the DB
  python -m src.utils.db_admin migrate      # Create any new tables only
  python -m src.utils.db_admin clear-data   # Remove games/characters/universes
"""

import argparse
from pathlib import Path
import psycopg2
from src.db.game_db import get_db_config

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def connect(db_name: str | None = None):
    """Return a new database connection."""
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg.get("DB_HOST", "localhost"),
        port=cfg.get("DB_PORT", 5432),
        dbname=db_name or cfg.get("DB_NAME", "influence_rpg"),
        user=cfg.get("DB_USER", "postgres"),
        password=cfg.get("DB_PASSWORD", "postgres"),
    )


def execute_sql_file(conn, path: Path):
    """Execute the SQL file located at *path* using the provided connection."""
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def rebuild():
    """Drop and recreate the entire database."""
    cfg = get_db_config()
    target = cfg.get("DB_NAME", "influence_rpg")

    admin = connect("postgres")
    admin.autocommit = True
    try:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {target};")
            cur.execute(f"CREATE DATABASE {target};")
    finally:
        admin.close()

    conn = connect(target)
    try:
        execute_sql_file(conn, SQL_DIR / "db_setup.sql")
        execute_sql_file(conn, SQL_DIR / "rulesets.sql")
        execute_sql_file(conn, SQL_DIR / "universes_setup.sql")
    finally:
        conn.close()


def migrate():
    """Create any new tables without touching existing ones."""
    conn = connect()
    try:
        execute_sql_file(conn, SQL_DIR / "db_setup.sql")
        execute_sql_file(conn, SQL_DIR / "rulesets.sql")
        execute_sql_file(conn, SQL_DIR / "universes_setup.sql")
    finally:
        conn.close()


def clear_data():
    """Delete all games, characters and universes but keep rulesets."""
    conn = connect()
    try:
        execute_sql_file(conn, SQL_DIR / "full_wipe.sql")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Influence RPG DB admin")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rebuild", help="Drop and recreate the entire database")
    sub.add_parser("migrate", help="Create new tables without modifying existing ones")
    sub.add_parser("clear-data", help="Delete games, characters and universes")

    args = parser.parse_args()

    if args.cmd == "rebuild":
        rebuild()
    elif args.cmd == "migrate":
        migrate()
    elif args.cmd == "clear-data":
        clear_data()


if __name__ == "__main__":
    main()
