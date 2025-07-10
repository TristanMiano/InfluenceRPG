"""
RAG Retrieval Module for InfluenceRPG

This module embeds a free-text query and retrieves the top-K most similar
chunks from the `ruleset_chunks` table using PostgreSQL's vector similarity (<->) operator.

Dependencies:
  pip install sentence-transformers psycopg2-binary

Place this file at: src/game/rag.py
"""
import logging

from sentence_transformers import SentenceTransformer
from src.db.character_db import get_db_connection

# Load the embedding model once, falling back to a dummy model if download fails
try:
    _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:  # pragma: no cover - network/offline fallback
    logging.error(f"Could not load embedding model: {e}")

    class _DummyModel:
        def encode(self, texts):
            # Return a fixed-size zero vector for each text
            return [[0.0] * 384 for _ in texts]

    _embedding_model = _DummyModel()
# Default number of chunks to retrieve
DEFAULT_TOP_K = 5


def embed_query(query: str) -> list[float]:
    """
    Convert a text query into a vector embedding.
    """
    try:
        emb = _embedding_model.encode([query])[0]
        return emb.tolist()
    except Exception as e:
        logging.error(f"Failed to embed query: {e}")
        return []


def retrieve_chunks(ruleset_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> list[str]:
    """
    Embed the query, then fetch the top_k most similar ruleset chunks.

    Args:
        ruleset_id: UUID of the ruleset to search within.
        query:      Free-text query (e.g. universe + game description).
        top_k:      Number of chunks to return.

    Returns:
        List of chunk_text strings, ordered most similar first.
    """
    embedding = embed_query(query)
    if not embedding:
        return []

    # Convert embedding list to pgvector literal '[f1,f2,...]'
    vec_literal = "[" + ",".join(str(x) for x in embedding) + "]"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_text
                  FROM ruleset_chunks
                 WHERE ruleset_id = %s
                 ORDER BY embedding <-> %s::vector
                 LIMIT %s
                """,
                (ruleset_id, vec_literal, top_k)
            )
            rows = cur.fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logging.error(f"Error retrieving chunks for ruleset {ruleset_id}: {e}")
        return []
    finally:
        conn.close()
