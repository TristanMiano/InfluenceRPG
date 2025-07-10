import json
import pytest
from fastapi.testclient import TestClient

from src.server.main import app

# Unit test for run_branch

def test_run_branch(monkeypatch):
    from src.game import brancher

    created = []
    statuses = {}
    joins = {}
    messages = []
    links = []
    events = []
    branches = []

    def fake_create_game(name):
        gid = f"g{len(created)+1}"
        g = {"id": gid, "name": name, "status": "waiting"}
        created.append(g)
        return g

    def fake_join_game(gid, cid):
        joins.setdefault(gid, []).append(cid)

    def fake_update_status(gid, status):
        statuses[gid] = status

    def fake_get_game(gid):
        if gid == "orig":
            return {"id": "orig", "name": "Original", "status": "active"}
        for g in created:
            if g["id"] == gid:
                return g
        return None

    def fake_save_chat_message(gid, sender, msg):
        messages.append((gid, sender, msg))

    def fake_get_latest_summary(gid):
        return "summary"

    def fake_list_universes_for_game(gid):
        return ["u1"]

    def fake_add_game_to_universe(uid, gid):
        links.append((uid, gid))

    def fake_record_branch(orig, new_ids, info):
        branches.append((orig, new_ids, info))

    def fake_record_event(universe_id, game_id, event_type, payload):
        events.append((universe_id, game_id, event_type, payload))

    def fake_notify_branch(orig, results):
        events.append(("notify", orig, results))

    monkeypatch.setattr(brancher, "create_game", fake_create_game)
    monkeypatch.setattr(brancher, "join_game", fake_join_game)
    monkeypatch.setattr(brancher, "update_game_status", fake_update_status)
    monkeypatch.setattr(brancher, "get_game", fake_get_game)
    monkeypatch.setattr(brancher, "save_chat_message", fake_save_chat_message)
    monkeypatch.setattr(brancher, "get_latest_game_summary", fake_get_latest_summary)
    monkeypatch.setattr(brancher.universe_db, "list_universes_for_game", fake_list_universes_for_game)
    monkeypatch.setattr(brancher.universe_db, "add_game_to_universe", fake_add_game_to_universe)
    monkeypatch.setattr(brancher.universe_db, "record_branch", fake_record_branch)
    monkeypatch.setattr(brancher.universe_db, "record_event", fake_record_event)
    monkeypatch.setattr(brancher, "notify_branch", fake_notify_branch)

    groups = [{"character_ids": ["c1"], "description": "test"}]
    res = brancher.run_branch("orig", groups)

    assert statuses.get("orig") == "branched"
    assert branches
    assert any(ev[1] == created[0]["id"] for ev in events if ev[0] == "u1")
    assert ("notify", "orig", res) in events

# API endpoint test

def test_branch_endpoint(monkeypatch):
    from src.server import game as game_router
    from src.game import brancher

    def fake_authenticate_user(u, p):
        return {"username": u, "role": "player"}

    def fake_list_players(game_id):
        return ["c1"]

    called = {}

    def fake_run_branch(gid, groups, send_notifications=True):
        called["groups"] = groups
        return [{"game": {"id": "n1", "name": "new", "status": "waiting"}, "character_ids": ["c1"]}]

    monkeypatch.setattr("src.auth.auth.authenticate_user", fake_authenticate_user)
    monkeypatch.setattr(game_router.game_db, "list_players_in_game", fake_list_players)
    monkeypatch.setattr(game_router, "run_branch", fake_run_branch)
    monkeypatch.setattr(game_router, "notify_branch", lambda *a, **k: called.setdefault("notify", True))
    monkeypatch.setattr(game_router.universe_db, "list_universes_for_game", lambda gid: [])
    monkeypatch.setattr(game_router, "_add_universe_names", lambda g: g)

    client = TestClient(app)
    client.post("/login", json={"username": "u", "password": "p"})
    resp = client.post("/api/game/orig/branch", json={"groups": [{"character_ids": ["c1"], "description": ""}]})
    assert resp.status_code == 200
    assert called.get("notify") is True
    assert called["groups"]

# WebSocket branch flow

def test_websocket_branch(monkeypatch):
    from src.server import game_chat
    from src.game import brancher
    from src.game import tools

    monkeypatch.setattr(game_chat.game_db, "list_chat_messages", lambda gid: [])
    monkeypatch.setattr(game_chat.game_db, "get_game", lambda gid: {"id": gid, "name": "Base", "status": "active"})
    monkeypatch.setattr(game_chat.game_db, "save_chat_message", lambda *a, **k: None)
    monkeypatch.setattr(game_chat.game_db, "list_players_in_game", lambda gid: ["c1"])
    monkeypatch.setattr(game_chat.universe_db, "list_universes_for_game", lambda gid: [])
    monkeypatch.setattr(game_chat, "get_character_by_id", lambda cid: {"id": cid, "name": "Char", "owner": "u"})
    monkeypatch.setattr(tools, "plan_tool_calls", lambda h, g: {"branch": {"groups": [{"character_ids": ["c1"], "description": ""}]}} if g.startswith("branch") else {})
    monkeypatch.setattr(brancher, "notify_branch", lambda *a, **k: None)
    monkeypatch.setattr(brancher, "create_game", lambda name: {"id": "n1", "name": name, "status": "waiting"})
    monkeypatch.setattr(brancher, "join_game", lambda *a, **k: None)
    monkeypatch.setattr(brancher, "update_game_status", lambda *a, **k: None)
    monkeypatch.setattr(brancher, "get_game", lambda gid: {"id": gid, "name": "Base", "status": "active"})
    monkeypatch.setattr(brancher, "get_latest_game_summary", lambda gid: "")
    monkeypatch.setattr(brancher.universe_db, "add_game_to_universe", lambda *a, **k: None)
    monkeypatch.setattr(brancher.universe_db, "list_universes_for_game", lambda gid: [])
    monkeypatch.setattr(brancher.universe_db, "record_branch", lambda *a, **k: None)
    monkeypatch.setattr(brancher.universe_db, "record_event", lambda *a, **k: None)

    client = TestClient(app)
    with client.websocket_connect("/ws/game/base/chat?username=u&character_id=c1") as ws:
        ws.send_text("/gm branch {}")
        data = ws.receive_text()
        assert "Game branched" in data
        ws.send_text("hello")
        second = ws.receive_text()
        assert "hello" in second
