import json
from fastapi.testclient import TestClient
from src.server.main import app


def test_character_wizard_dice(monkeypatch):
    from src.server import character_wizard as cw

    def fake_get_ruleset(rid):
        return {"id": rid, "char_creation": "rules"}

    calls = {"step": 0}

    def fake_generate(prompt, conversation_context="", max_retries=3):
        if calls["step"] == 0:
            calls["step"] = 1
            return json.dumps({
                "tool_calls": {"dice": {"num_rolls": 2, "sides": 6}},
                "narrative": "rolling"
            })
        else:
            assert "Dice results" in prompt
            return json.dumps({"name": "Hero", "character_data": {"str": 10}})

    monkeypatch.setattr(cw, "get_ruleset", fake_get_ruleset)
    monkeypatch.setattr(cw, "generate_completion", fake_generate)

    client = TestClient(app)
    resp = client.post("/api/character/wizard", json={"ruleset_id": "r1", "history": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["complete"] is True
    assert data["name"] == "Hero"
    assert data["character_data"]["str"] == 10
