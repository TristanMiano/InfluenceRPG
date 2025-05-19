#!/usr/bin/env python3
"""
import_ruleset.py

Usage:
  python -m src.utils.import_ruleset \
    --pdf path/to/ruleset.pdf \
    --name "My Great Ruleset" \
    [--description "Optional summary"]

Installs needed:
  pip install pdfminer.six sentence-transformers psycopg2-binary
"""

import argparse, sys, uuid
from pathlib import Path
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values
from src.db.character_db import get_db_connection  # re-uses your DB config

def chunk_text(text: str, size: int = 4000):
    return [text[i : i + size] for i in range(0, len(text), size)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf",         required=True, help="Path to PDF file")
    parser.add_argument("--name",        required=True, help="Ruleset name")
    parser.add_argument("--description", default="",   help="Short description")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: {pdf_path} does not exist", file=sys.stderr)
        sys.exit(1)

    print("Extracting text from PDF…")
    full_text = extract_text(str(pdf_path))

    print("Connecting to database…")
    conn = get_db_connection()
    try:
        # 1) Insert into rulesets
        rs_id = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rulesets (id, name, description, full_text)
                VALUES (%s, %s, %s, %s)
                """,
                (rs_id, args.name, args.description, full_text)
            )
        conn.commit()

        # 2) Chunk & embed
        print("Chunking text…")
        chunks = chunk_text(full_text, size=4000)
        print(f"{len(chunks)} chunks created. Generating embeddings…")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(chunks)

        # 3) Bulk insert into ruleset_chunks
        print("Inserting chunks…")
        records = [
            (rs_id, idx, chunk, emb.tolist())
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO ruleset_chunks
                  (ruleset_id, chunk_index, chunk_text, embedding)
                VALUES %s
                """,
                records
            )
        conn.commit()
        print("Done! Ruleset ID =", rs_id)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
