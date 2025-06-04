# src/server/game_chat.py

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime, timezone
from src.db import game_db, universe_db
from src.db.game_db import list_chat_messages, get_db_connection
from sentence_transformers import SentenceTransformer
from src.llm.gm_llm import generate_gm_response
from src.db.character_db import get_character_by_id
from src.game.conflict_detector import run_conflict_detector

router = APIRouter()

summary_model = SentenceTransformer("all-MiniLM-L6-v2")

# Global conversation history storage per game instance.
conversation_histories: Dict[str, List[str]] = {}

# Track, per‐game, the latest news‐timestamp we've already included in a GM prompt
last_included_news_time: Dict[str, datetime] = {}

class GameConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)
        if game_id not in conversation_histories:
            conversation_histories[game_id] = []
        # Initialize last_included_news_time if not set
        if game_id not in last_included_news_time:
            # Start with epoch so that the first time we include any news
            last_included_news_time[game_id] = datetime.fromtimestamp(0, tz=timezone.utc)

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.active_connections and websocket in self.active_connections[game_id]:
            self.active_connections[game_id].remove(websocket)

    async def broadcast(self, game_id: str, message: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                await connection.send_text(message)

manager = GameConnectionManager()

@router.websocket("/ws/game/{game_id}/chat")
async def game_chat_endpoint(game_id: str, websocket: WebSocket):
    # 1. Extract account & character IDs
    username     = websocket.query_params.get("username", "unknown")
    character_id = websocket.query_params.get("character_id", "unknown")

    # 2. Lookup the character’s name
    try:
        char = get_character_by_id(character_id)
        character_name = char["name"] if char else "unknown"
    except Exception:
        character_name = "unknown"

    # 3. Combine into a display name
    sender_display = f"{character_name} ({username})"

    # 4. Register this connection
    await manager.connect(game_id, websocket)

    # 4.1 Load & send existing messages from the DB to this socket
    if not conversation_histories.get(game_id):
        conversation_histories[game_id] = []

    # Pull everything from chat_messages table
    persisted = list_chat_messages(game_id)
    for msg in persisted:
        entry = f"{msg['sender']}: {msg['message']}"
        conversation_histories[game_id].append(entry)
        # send each past message just to this new client
        await websocket.send_text(json.dumps({
            "game_id":   game_id,
            "sender":    msg["sender"],
            "message":   msg["message"],
            "timestamp": msg["timestamp"].isoformat() + "Z"
        }))

    # 5. Log & broadcast a “join” event for both players and GM context
    join_msg = f"{sender_display} has joined the game."
    system_entry = f"System: {join_msg}"
    conversation_histories[game_id].append(system_entry)

    await manager.broadcast(game_id, json.dumps({
        "game_id": game_id,
        "sender": "System",
        "message": join_msg,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }))

    # 5.1 Broadcast full character details so the GM knows their stats
    try:
        full_char = get_character_by_id(character_id) or {}
        char_data = full_char.get("character_data", {})
        attrs_msg = f"{character_name}'s full profile: {json.dumps(char_data)}"
        conversation_histories[game_id].append(f"System: {attrs_msg}")
        await manager.broadcast(game_id, json.dumps({
            "game_id":   game_id,
            "sender":    "System",
            "message":   attrs_msg,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }))
    except Exception as e:
        print(f"Error broadcasting character data: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            stripped = data.strip()

            # --- /gm commands branch ---
            if stripped.startswith("/gm"):
                parts = stripped.split(maxsplit=2)
                cmd = parts[1] if len(parts) > 1 else ""

                # 1) Summarize new chat since last summary
                if cmd == "summarize":
                    # (Unchanged from before…)

                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT max(summary_date) FROM game_history WHERE game_id=%s",
                            (game_id,)
                        )
                        last_dt = cur.fetchone()[0]  # may be None

                        if last_dt:
                            cur.execute(
                                "SELECT sender, message FROM chat_messages "
                                "WHERE game_id=%s AND timestamp > %s ORDER BY timestamp",
                                (game_id, last_dt)
                            )
                        else:
                            cur.execute(
                                "SELECT sender, message FROM chat_messages "
                                "WHERE game_id=%s ORDER BY timestamp",
                                (game_id,)
                            )
                        rows = cur.fetchall()
                    conn.close()

                    convo = "\n".join(f"{r[0]}: {r[1]}" for r in rows)
                    summary_prompt = (
                        "Please provide a concise summary of the following game chat:\n\n"
                        f"{convo}"
                    )
                    summary_text = generate_gm_response(summary_prompt) \
                                   if summary_prompt.strip() else ""

                    embedding = summary_model.encode(summary_text).tolist()

                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO game_history (game_id, summary, embedding) VALUES (%s, %s, %s)",
                            (game_id, summary_text, embedding)
                        )
                        conn.commit()
                    conn.close()

                    # Record this summary as a universe event
                    universe_ids = universe_db.list_universes_for_game(game_id)
                    for uni in universe_ids:
                        universe_db.record_event(
                            universe_id=uni,
                            game_id=game_id,
                            event_type="gm_summary",
                            event_payload={"summary": summary_text}
                        )

                    # Run conflict detection
                    for uni in universe_ids:
                        run_conflict_detector(uni)

                    note = f"[Summary generated at {datetime.utcnow().isoformat()}]"
                    conversation_histories[game_id].append(f"System: {note}")
                    await manager.broadcast(game_id, json.dumps({
                        "game_id":   game_id,
                        "sender":    "System",
                        "message":   note,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }))

                # 2) Show history of summaries
                elif cmd == "history":
                    # (Unchanged from before…)
                    k = None
                    if len(parts) > 2 and parts[2].isdigit():
                        k = int(parts[2])

                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        if k:
                            cur.execute(
                                "SELECT summary_date, summary FROM game_history "
                                "WHERE game_id=%s ORDER BY summary_date DESC LIMIT %s",
                                (game_id, k)
                            )
                        else:
                            cur.execute(
                                "SELECT summary_date, summary FROM game_history "
                                "WHERE game_id=%s ORDER BY summary_date DESC",
                                (game_id,)
                            )
                        summaries = cur.fetchall()
                    conn.close()

                    for dt, text in summaries:
                        msg = f"[{dt.isoformat()}] {text}"
                        await manager.broadcast(game_id, json.dumps({
                            "game_id":   game_id,
                            "sender":    "History",
                            "message":   msg,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }))

                # 3) Fallback: narrative GM
                else:
                    # --- NEW: Fetch recent universe news, up to 5 items newer than last_included_news_time ---
                    # Determine the first universe this game is in (if any)
                    universe_ids = universe_db.list_universes_for_game(game_id)
                    news_block = ""
                    if universe_ids:
                        uni = universe_ids[0]
                        # Get all recent news items (limit 5)
                        raw_news = universe_db.list_news(uni, limit=5)
                        # Filter only those strictly newer than last_included_news_time
                        newest_allowed = last_included_news_time.get(game_id)
                        fresh_items = []
                        for item in raw_news:
                            published = item["published_at"]
                            # Make sure both are timezone-aware UTC
                            if published.tzinfo is None:
                                published = published.replace(tzinfo=timezone.utc)
                            if newest_allowed is None or published > newest_allowed:
                                fresh_items.append(item)

                        if fresh_items:
                            # Build a short “Recent Universe News” block
                            lines = [
                                f"Recent Universe News (as of {datetime.utcnow().isoformat()}Z):"
                            ]
                            # Sort by published_at ascending so oldest of the fresh first
                            fresh_items.sort(key=lambda x: x["published_at"])
                            for idx, itm in enumerate(fresh_items, start=1):
                                ts = itm["published_at"].astimezone(timezone.utc).isoformat()
                                summary = itm["summary"].replace("\n", " ").strip()
                                lines.append(f"{idx}) [{ts}] {summary}")
                                # Update our last included timestamp
                                if itm["published_at"] > last_included_news_time[game_id]:
                                    last_included_news_time[game_id] = itm["published_at"]
                            news_block = "\n".join(lines) + "\n\n"
                        else:
                            # No new items since last time: no block
                            news_block = ""
                    else:
                        news_block = ""

                    # --- Build the conversation context as before ---
                    if stripped.startswith("/gm"):
                        gm_prompt = stripped[3:].strip() or "Provide a narrative update."
                    else:
                        # If it somehow was not a /gm (rare), treat as default
                        gm_prompt = "Provide a narrative update."

                    full_history = "\n".join(conversation_histories[game_id])

                    # Prepend news_block before “Conversation History”
                    assembled_prompt = f"{news_block}Conversation History:\n{full_history}\n\nUser (trigger): {gm_prompt}\n\nGM Response:"

                    # Call the GM LLM
                    gm_response = generate_gm_response(assembled_prompt)

                    # Persist & broadcast GM output
                    game_db.save_chat_message(game_id, "GM", gm_response)
                    conversation_histories[game_id].append(f"GM: {gm_response}")
                    await manager.broadcast(game_id, json.dumps({
                        "game_id":   game_id,
                        "sender":    "GM",
                        "message":   gm_response,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }))

            # --- Player message branch ---
            else:
                # a) Persist & append to GM context
                game_db.save_chat_message(game_id, sender_display, data)
                conversation_histories[game_id].append(f"{sender_display}: {data}")

                # b) Broadcast to all players
                await manager.broadcast(game_id, json.dumps({
                    "game_id":   game_id,
                    "sender":    sender_display,
                    "message":   data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }))
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
