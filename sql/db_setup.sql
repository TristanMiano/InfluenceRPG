-- db_setup.sql
-- ========================================================
-- Before running this script, ensure that the database
-- 'influence_rpg' exists. If it does not, create it manually:
--
--   psql -U postgres -c "CREATE DATABASE influence_rpg;"
--
-- Then connect to the 'influence_rpg' database and run this script.
-- ========================================================

-- Table for Users (optional, but useful for persistent authentication)
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for Characters
CREATE TABLE IF NOT EXISTS characters (
    id UUID PRIMARY KEY,
    owner VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    character_class VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_owner
        FOREIGN KEY(owner)
            REFERENCES users(username)
            ON DELETE CASCADE
);

-- Table for Games
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Join Table for Game Participants (mapping characters to games)
CREATE TABLE IF NOT EXISTS game_players (
    game_id UUID NOT NULL,
    character_id UUID NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (game_id, character_id),
    CONSTRAINT fk_game
        FOREIGN KEY (game_id)
            REFERENCES games(id)
            ON DELETE CASCADE,
    CONSTRAINT fk_character
        FOREIGN KEY (character_id)
            REFERENCES characters(id)
            ON DELETE CASCADE
);

-- Table for Chat Messages (to store game chat logs)
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL,
    sender VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_game_chat
        FOREIGN KEY (game_id)
            REFERENCES games(id)
            ON DELETE CASCADE
);

-- You must build pgvector on your platform before running the following.

-- Run as a superuser in your database:
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_embeddings (
  id          SERIAL PRIMARY KEY,
  file_path   TEXT        NOT NULL,       -- e.g. 'reference/chap1.txt'
  content     TEXT        NOT NULL,       -- full text to embed
  embedding   VECTOR(384) NOT NULL,      -- adjust dim to your model (e.g. 1536 for OpenAI ada)
  metadata    JSONB       DEFAULT '{}' ,  -- e.g. {"source":"manual","tags":["rules"]}
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat is a good compromise of speed & accuracy; set lists ≈ √N 
CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding
  ON document_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- After creating the index:
VACUUM ANALYZE document_embeddings;
