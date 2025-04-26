Here’s a minimal end-to-end example of how you’d wire up PostgreSQL + pgvector for a RAG‐style workflow.

---

## 1. Install & enable the pgvector extension

```sql
-- As a superuser in your database:
CREATE EXTENSION IF NOT EXISTS vector;
```

> This gives you a new `vector` column type and the `<->` distance operator.

---

## 2. Define your documents table

```sql
CREATE TABLE documents (
  id        SERIAL PRIMARY KEY,
  content   TEXT            NOT NULL,
  embedding VECTOR(1536),       -- match your embedding dimension!
  metadata  JSONB           NULL
);
```

- **`content`** holds the raw text chunk.  
- **`embedding`** is a fixed-size vector (here: 1 536 dims for OpenAI’s text-embedding-ada-002).  
- **`metadata`** can store source IDs, dates, tags, etc.

---

## 3. Create an approximate‐NN index

```sql
-- IVFFlat is usually a good balance of speed & accuracy:
CREATE INDEX ON documents
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

- After creating this index, you must `VACUUM ANALYZE documents;` so it can build its internal structure.

---

## 4. Ingest (insert) embeddings

Here’s a Python snippet using `psycopg2` and OpenAI’s embeddings API:

```python
import openai, psycopg2

# 1. Compute the embedding for your text chunk
resp = openai.Embedding.create(
    model="text-embedding-ada-002",
    input=" …your document chunk here …"
)
vec = resp["data"][0]["embedding"]  # a list of 1536 floats

# 2. Insert into Postgres
conn = psycopg2.connect("postgresql://user:pass@host:5432/mydb")
cur = conn.cursor()
cur.execute(
    """
    INSERT INTO documents (content, embedding, metadata)
    VALUES (%s, %s, %s)
    """,
    (
      "…your document chunk here…",
      vec,
      {"source": "report.pdf", "page": 4}
    )
)
conn.commit()
```

---

## 5. Query (retrieve nearest neighbors)

When a user asks a question, you:

1. Embed the query text.  
2. Ask Postgres for the closest chunks.

```python
# 1. Embed the user question
qvec = openai.Embedding.create(
    model="text-embedding-ada-002",
    input="What were the key findings on X?"
)["data"][0]["embedding"]

# 2. Retrieve top-K similar chunks
cur.execute(
    """
    SELECT id, content, metadata
    FROM documents
    ORDER BY embedding <-> %s
    LIMIT 5
    """,
    (qvec,)
)
rows = cur.fetchall()
for doc_id, content, meta in rows:
    print(f"[{doc_id}] {content[:100]}… (meta={meta})")
```

- The `<->` operator uses cosine distance by default with `vector_cosine_ops`.  
- You can combine with standard SQL filters too:
  ```sql
  WHERE metadata->>'source' = 'report.pdf'
  ```

---

## 6. Putting it all together in a RAG pipeline

1. **Chunk & embed** your entire corpus ahead of time (batch job).  
2. **On each user query**:  
   - Embed the query  
   - `SELECT … ORDER BY embedding <-> $1 LIMIT K`  
   - Assemble those chunks into your LLM prompt (with any instruction template)  
   - Call the LLM to generate the answer  

By leveraging Postgres + pgvector, you get a single, unified store for both your vectors **and** your metadata, with full SQL power for filtering, joining, and security controls—no external vector-DB service required.