-- ================================================
-- Game Universe: shared‐world event & news support
-- ================================================

-- Universes gets run AFTER db_setup.sql and rulesets.sql

-- 1. Universes table
CREATE TABLE IF NOT EXISTS universes (
    id          UUID        PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
	ruleset_id UUID NOT NULL
	CONSTRAINT fk_universe_ruleset
      REFERENCES rulesets(id)
      ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Map games into universes
CREATE TABLE IF NOT EXISTS universe_games (
    universe_id UUID    NOT NULL
        CONSTRAINT fk_universe
            REFERENCES universes(id)
            ON DELETE CASCADE,
    game_id     UUID    NOT NULL
        CONSTRAINT fk_game
            REFERENCES games(id)
            ON DELETE CASCADE,
    joined_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (universe_id, game_id)
);

-- 3. Event store for universes
CREATE TABLE IF NOT EXISTS universe_events (
    id             SERIAL PRIMARY KEY,
    universe_id    UUID    NOT NULL
        CONSTRAINT fk_universe_events
            REFERENCES universes(id)
            ON DELETE CASCADE,
    game_id        UUID    NOT NULL
        CONSTRAINT fk_game_events
            REFERENCES games(id)
            ON DELETE CASCADE,
    event_type     VARCHAR(100) NOT NULL,
    event_payload  JSONB   NOT NULL,
    event_time     TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Conflict detector log
CREATE TABLE IF NOT EXISTS conflict_detections (
    id             SERIAL PRIMARY KEY,
    universe_id    UUID    NOT NULL
        CONSTRAINT fk_conflict_universe
            REFERENCES universes(id)
            ON DELETE CASCADE,
    conflict_info  JSONB   NOT NULL,
    detected_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Merger records
CREATE TABLE IF NOT EXISTS mergers (
    id                SERIAL PRIMARY KEY,
    universe_id       UUID    NOT NULL
        CONSTRAINT fk_merger_universe
            REFERENCES universes(id)
            ON DELETE CASCADE,
    from_instance_ids JSONB   NOT NULL,
    into_instance_id  UUID    NOT NULL
        CONSTRAINT fk_merger_into
            REFERENCES games(id)
            ON DELETE CASCADE,
    merged_at         TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Branch records
CREATE TABLE IF NOT EXISTS game_branches (
    id             SERIAL PRIMARY KEY,
    original_game  UUID    NOT NULL
        CONSTRAINT fk_branch_original
            REFERENCES games(id)
            ON DELETE CASCADE,
    new_game_ids   JSONB   NOT NULL,
    branch_info    JSONB   NOT NULL,
    branched_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Published universe‐level news
CREATE TABLE IF NOT EXISTS universe_news (
    id            SERIAL PRIMARY KEY,
    universe_id   UUID    NOT NULL
        CONSTRAINT fk_news_universe
            REFERENCES universes(id)
            ON DELETE CASCADE,
    summary       TEXT    NOT NULL,
    published_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Named entities recognized across games in a universe
CREATE TABLE IF NOT EXISTS named_entities (
    id UUID PRIMARY KEY,
    universe_id UUID NOT NULL
        CONSTRAINT fk_entity_universe
            REFERENCES universes(id)
            ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    description TEXT,
    player_character BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (universe_id, name)
);
