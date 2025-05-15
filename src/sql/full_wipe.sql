BEGIN;

-- Child tables first
DELETE FROM game_players;
DELETE FROM chat_messages;
DELETE FROM game_history;
DELETE FROM universe_events;
DELETE FROM conflict_detections;
DELETE FROM mergers;
DELETE FROM universe_news;
DELETE FROM universe_games;

-- Then parent tables
DELETE FROM games;
DELETE FROM characters;
DELETE FROM universes;

COMMIT;
