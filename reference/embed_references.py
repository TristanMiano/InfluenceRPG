#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path
import psycopg2
from sentence_transformers import SentenceTransformer

# ─── CONFIGURATION ────────────────────────────────────────────────────────────────

# adjust these to suit your chunk-size needs:
MAX_CHARS   = 1000
OVERLAP     = 200

# postgres config file, relative to this script:
DB_CONFIG_PATH = Path(__file__).parent.parent / "config" / "db_config.json"

# ─── HELPERS ──────────────────────────────────────────────────────────────────────

def load_db_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection(cfg):
    return psycopg2.connect(
        host   = cfg["DB_HOST"],
        port   = cfg["DB_PORT"],
        dbname = cfg["DB_NAME"],
        user   = cfg["DB_USER"],
        password = cfg["DB_PASSWORD"]
    )

def chunk_text(text, max_chars=MAX_CHARS, overlap=OVERLAP):
    """Simple sliding‐window chunker on characters."""
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks

# ─── MAIN ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Embed all files under reference/ and upsert into document_embeddings."
    )
    parser.add_argument(
        "--reembed",
        action="store_true",
        help="If set, delete any existing rows for a file_path before inserting."
    )
    args = parser.parse_args()

    # load model once
    print("Loading embedding model…")
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")

    # load DB config & connect
    db_cfg = load_db_config(DB_CONFIG_PATH)
    conn = get_db_connection(db_cfg)
    cur  = conn.cursor()

    # Walk reference folder
    ref_dir = Path(__file__).parent
    script_name = Path(__file__).name

    for root, dirs, files in os.walk(ref_dir):
        for fname in files:
            if fname in (script_name, "README.md"):
                continue
            file_path = Path(root) / fname
            if not file_path.suffix.lower() in (".txt", ".md"):
                continue

            rel_path = str(file_path.relative_to(ref_dir))
            print(f"\n---\nProcessing '{rel_path}'")

            # optionally clear old embeddings
            if args.reembed:
                cur.execute(
                    "DELETE FROM document_embeddings WHERE file_path = %s",
                    (rel_path,)
                )
                conn.commit()

            text = file_path.read_text(encoding="utf-8")
            chunks = chunk_text(text)
            total = len(chunks)
            print(f"  → {total} chunks")

            # embed & insert
            for i, chunk in enumerate(chunks, start=1):
                print(f"    • embedding chunk {i}/{total}", end="\r")
                emb = model.encode(chunk, normalize_embeddings=True)
                # represent as pgvector literal, e.g. '[0.123,0.456,…]'
                vec_literal = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"
                metadata = {"file": rel_path, "chunk_index": i-1}

                cur.execute(
                    """
                    INSERT INTO document_embeddings
                      (file_path, content, embedding, metadata, created_at, updated_at)
                    VALUES
                      (%s, %s, %s::vector, %s, NOW(), NOW())
                    """,
                    (rel_path, chunk, vec_literal, json.dumps(metadata))
                )

            conn.commit()
            print(f"  ✓ done '{rel_path}' ({total} chunks)")

    cur.close()
    conn.close()
    print("\nAll done!")

if __name__ == "__main__":
    main()
