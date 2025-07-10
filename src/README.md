# Source Directory (src) README

This document describes the architecture, technology stack, and high‑level flow of the `src/` directory for the Influence RPG prototype server.

---

## 1. Architecture Overview

The `src/` directory is organized into logical layers:

1. **API Layer** (`src/server`)

   * Implements HTTP and WebSocket endpoints via **FastAPI**.
   * Handles authentication, game creation/joining, universe management, ruleset CRUD, character wizards, and real‑time chat.
   * Serves static assets (JS/CSS) compiled by **Vite** with long‑term caching.

2. **Domain & Game Logic** (`src/game`)

   * **Conflict Detector**: Uses LLM to detect overlapping game events and triggers mergers.
   * **Merger**: Automates merging of game instances in the same universe.
   * **News Extractor**: Summarizes recent events into in‑universe bulletins via LLM.

3. **Data Access Layer** (`src/db`)

   * Database modules for **PostgreSQL** (via `psycopg2` + `RealDictCursor`): users, characters, games, chat, universes, rulesets, embeddings, and history.
   * Enforces constraints (e.g., one character per universe, one instance per game).
   * Integrates **pgvector** extension for RAG and similarity search.

4. **LLM Integration** (`src/llm`)

   * Generic client (`llm_client.py`) loads config and communicates with Google Gemini (or simulates responses).
   * Domain‑specific wrappers: `gm_llm` for narrative, `initial_prompt` for opening scenes, summarization fallbacks.

5. **Data Models** (`src/models`)

   * Pydantic schemas for Characters, Games, Users.

6. **Utilities & Scripts** (`src/utils`)

   * Account creation, PDF ruleset import, chunking & embedding, summarization scripts, security (password hashing).

7. **Tests** (`src/test`)

   * Basic FastAPI endpoint tests using `pytest` and `TestClient`.

---

## 2. Technology Stack

* **Python 3.11+**
* **FastAPI** (API & WebSockets)
* **Uvicorn/ASGI** server
* **PostgreSQL** with **psycopg2-binary**
* **pgvector** for embedding storage & similarity search
* **Pydantic** for request/response validation
* **Sentence Transformers** (`all-MiniLM-L6-v2`) for embeddings
* **Google Gemini API** (optional) for LLM completions
* **tiktoken** for token counting
* **Vite** + **JSX/React** for character wizard
* **Jinja2** for server‑side HTML templates
* **python-dotenv** for loading environment variables
* **pdfminer.six** for parsing PDF rulesets

---

## 3. High‑Level Flow

1. **Startup**: Load manifest, mount static files, and launch an asyncio background task that runs the news extractor every 30 min.
2. **Authentication**: `/login` and account creation endpoints use hashed passwords.
3. **Character Creation**: Wizard flow (`/api/character/wizard`) iteratively collects data via LLM.
4. **Game Lifecycle**:

   * **Create**: `/api/game/create` checks for active characters, persists game, seeds with an AI‑generated opening scene.
   * **Join**: `/api/game/{id}/join`, enforces one‑character‑per‑game, persists join.
   * **Chat**: Real‑time WebSocket at `/ws/game/{id}/chat` broadcasts messages, persists them, and handles `/gm` commands for summaries, history, and ad‑hoc narrative generation.
5. **Universe Management**:

   * Create universes tied to rulesets.
   * List news and conflicts via REST; frontend polls every 30 s.
6. **Conflict & Merger**: After summaries or scheduled loop, detect conflicts and merge instances.

---

## 4. Configuration

1. **Database**: `config/db_config.json` (host, port, name, user, password).
2. **LLM**: `config/llm_config.json` (API key, default model).

---

## 5. Getting Started (src/ only)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt   # includes fastapi, psycopg2-binary, pydantic, sentence-transformers, tiktoken, requests

# 2. Configure DB & LLM
cp config/db_config.example.json config/db_config.json
cp config/llm_config.example.json config/llm_config.json
# edit credentials and keys

# 3. Run database migrations/setup
psql -U postgres -d influence_rpg -f src/sql/db_setup.sql
psql -U postgres -d influence_rpg -f src/sql/rulesets.sql
psql -U postgres -d influence_rpg -f src/sql/universes_setup.sql

# 4. Start the server
uvicorn src.server.main:app --reload  # or use `python src/server_control.py start` for background mode
```

---

## 6. Contribution & Testing

* Add new endpoints under `src/server`.
* Implement new game logic in `src/game`.
* DB changes: update SQL in `src/sql/`.
* Run tests: `pytest src/test`.

---

*This README describes only the `src/` subdirectory. For overall project info, refer to the root `README.md`.*
