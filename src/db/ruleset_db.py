# src/db/ruleset_db.py

import uuid
import json
from typing import List, Optional
from psycopg2.extras import RealDictCursor
from src.db.character_db import get_db_connection  # re-use your existing config

def create_ruleset(name: str, description: str, full_text: str) -> dict:
    """
    Inserts a new ruleset and returns its metadata.
    """
    rs_id = str(uuid.uuid4())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rulesets (id, name, description, full_text)
                VALUES (%s, %s, %s, %s)
                """,
                (rs_id, name, description, full_text)
            )
            conn.commit()
        return {"id": rs_id, "name": name, "description": description}
    finally:
        conn.close()

def list_rulesets() -> List[dict]:
    """
    Returns all rulesets (id, name, description, created_at).
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, description, created_at FROM rulesets ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()

def get_ruleset(rs_id: str) -> Optional[dict]:
    """
    Fetch a single ruleset by ID, including its full_text.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, description, full_text, created_at FROM rulesets WHERE id = %s",
                (rs_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def add_chunk(ruleset_id: str, chunk_index: int, chunk_text: str, embedding: List[float]):
    """
    Inserts one chunk and its embedding into ruleset_chunks.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ruleset_chunks
                  (ruleset_id, chunk_index, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (ruleset_id, chunk_index, chunk_text, embedding)
            )
            conn.commit()
    finally:
        conn.close()

def list_chunks(ruleset_id: str) -> List[dict]:
    """
    Retrieves all text chunks (with embeddings) for a ruleset in order.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT chunk_index, chunk_text, embedding
                  FROM ruleset_chunks
                 WHERE ruleset_id = %s
                 ORDER BY chunk_index
                """,
                (ruleset_id,)
            )
            return cur.fetchall()
    finally:
        conn.close()

def get_summary(ruleset_id: str) -> Optional[str]:
    """
    Return the cached summary for this ruleset, or None if not yet generated.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT summary FROM rulesets WHERE id = %s", (ruleset_id,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()

def set_summary(ruleset_id: str, summary: str):
    """
    Cache the provided summary in the DB so we only generate once.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE rulesets SET summary = %s WHERE id = %s",
                (summary, ruleset_id)
            )
            conn.commit()
    finally:
        conn.close()
