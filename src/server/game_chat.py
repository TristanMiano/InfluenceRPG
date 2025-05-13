# src/server/game_chat.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime
from src.db import game_db, universe_db  
from src.db.game_db import list_chat_messages, get_db_connection
from sentence_transformers import SentenceTransformer
from src.llm.gm_llm import generate_gm_response, generate_completion
from src.db.character_db import get_character_by_id   
from src.game.conflict_detector import run_conflict_detector

router = APIRouter()

summary_model = SentenceTransformer('all-MiniLM-L6-v2')

# Global conversation history storage per game instance.
conversation_histories: Dict[str, List[str]] = {}

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
    #     and seed our in-memory context for the GM.
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
    conversation_histories.setdefault(game_id, []).append(system_entry)

    await manager.broadcast(game_id, json.dumps({
        "game_id": game_id,
        "sender": "System",
        "message": join_msg,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }))
    
    # 5.1 Broadcast full character details so the GM knows their stats
    try:
        full_char = get_character_by_id(character_id) or {}
        # Expecting your character table to have a `character_data` JSON column
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
                    # find last summary timestamp
                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT max(summary_date) FROM game_history WHERE game_id=%s",
                            (game_id,)
                        )
                        last_dt = cur.fetchone()[0]  # may be None

                        # grab new chat_messages
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

                    # stitch into a prompt
                    convo = "\n".join(f"{r[0]}: {r[1]}" for r in rows)
                    summary_prompt = (
                        "Please provide a concise summary of the following game chat:\n\n"
                        f"{convo}"
                    )
                    summary_text = generate_completion(summary_prompt)

                    # embed it
                    embedding = summary_model.encode(summary_text).tolist()

                    # insert into game_history
                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO game_history (game_id, summary, embedding) VALUES (%s, %s, %s)",
                            (game_id, summary_text, embedding)
                        )
                        conn.commit()
                    conn.close()
                    
                    # --- record this summary as a universe‐event ---
                    # find all universes this game belongs to
                    universe_ids = universe_db.list_universes_for_game(game_id)
                    for uni in universe_ids:
                        universe_db.record_event(
                            universe_id=uni,
                            game_id=game_id,
                            event_type="gm_summary",
                            event_payload={"summary": summary_text}
                        )

                    # --- run conflict detection for this universe ---
                    for uni in universe_ids:
                        run_conflict_detector(uni)

                    # update in-memory context and broadcast
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
                    # parse optional k
                    k = None
                    if len(parts) > 2 and parts[2].isdigit():
                        k = int(parts[2])

                    # fetch from game_history
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

                    # broadcast each summary
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
                    gm_prompt = stripped[3:].strip() or "Provide a narrative update."
                    full_context = "\n".join(conversation_histories[game_id])
                    gm_response = generate_gm_response(
                        f"{full_context}\nUser (trigger): {gm_prompt}"
                    )
                    # persist & broadcast as before
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

