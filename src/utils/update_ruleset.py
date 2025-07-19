#!/usr/bin/env python3
"""Update the rulesets table from text files.

Each ruleset has its own directory under the project 'rules' folder containing
four files: ``full_text``, ``summary``, ``long_summary`` and ``char_creation``.
This script loads those files and updates (or inserts) the matching row in the
``rulesets`` table.
"""

import argparse
import uuid
from pathlib import Path
from src.db.character_db import get_db_connection

FIELDS = ["full_text", "summary", "long_summary", "char_creation"]


def load_ruleset_files(rs_dir: Path) -> dict:
    """Return a mapping of field -> text for the given ruleset directory."""
    data = {}
    for field in FIELDS:
        path = rs_dir / field
        data[field] = path.read_text(encoding="utf-8") if path.exists() else None
    return data


def upsert_ruleset(name: str, base_dir: Path) -> None:
    rs_dir = base_dir / name
    if not rs_dir.is_dir():
        raise FileNotFoundError(f"Ruleset directory not found: {rs_dir}")

    data = load_ruleset_files(rs_dir)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM rulesets WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                rs_id = row[0]
                cur.execute(
                    """
                    UPDATE rulesets
                       SET full_text = %s,
                           summary = %s,
                           long_summary = %s,
                           char_creation = %s
                     WHERE id = %s
                    """,
                    (
                        data["full_text"],
                        data["summary"],
                        data["long_summary"],
                        data["char_creation"],
                        rs_id,
                    ),
                )
            else:
                rs_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO rulesets
                        (id, name, description, full_text, summary, long_summary, char_creation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        rs_id,
                        name,
                        data["summary"] or "",
                        data["full_text"],
                        data["summary"],
                        data["long_summary"],
                        data["char_creation"],
                    ),
                )
            conn.commit()
        print(f"Ruleset '{name}' updated (id={rs_id}).")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Update rulesets table from files")
    parser.add_argument("--name", required=True, help="Ruleset directory and DB name")
    parser.add_argument(
        "--base-dir",
        default=Path(__file__).resolve().parents[2] / "rules",
        type=Path,
        help="Base directory containing ruleset folders",
    )
    args = parser.parse_args()
    upsert_ruleset(args.name, args.base_dir)


if __name__ == "__main__":
    main()
