-- 1) Create a table to hold each ruleset
CREATE TABLE IF NOT EXISTS rulesets (
  id           UUID      PRIMARY KEY,
  name         VARCHAR(255) NOT NULL UNIQUE,
  description  TEXT,
  full_text    TEXT      NOT NULL,       -- raw, PDF-extracted text
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 2) Chunked embeddings of each ruleset for RAG
CREATE TABLE IF NOT EXISTS ruleset_chunks (
  id            SERIAL    PRIMARY KEY,
  ruleset_id    UUID      NOT NULL
      CONSTRAINT fk_ruleset
        REFERENCES rulesets(id)
        ON DELETE CASCADE,
  chunk_index   INT       NOT NULL,      -- order of chunk
  chunk_text    TEXT      NOT NULL,      -- the chunk itself
  embedding     VECTOR(384) NOT NULL     -- adjust dim if you change models
);

-- 3) Index for similarity search
CREATE INDEX IF NOT EXISTS idx_ruleset_chunks_embedding
  ON ruleset_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);