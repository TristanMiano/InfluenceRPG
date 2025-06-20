# src/server/game_chat.py

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime, timezone
from src.db import game_db, universe_db
from src.db.game_db import list_chat_messages, get_db_connection, list_players_in_game
from sentence_transformers import SentenceTransformer
from src.llm.gm_llm import generate_gm_response
from src.game.tools import plan_tool_calls, roll_dice, query_ruleset_chunks
from src.db.character_db import get_character_by_id
from src.game.conflict_detector import run_conflict_detector
from src.server.notifications import notify_game_advanced
from src.utils.token_counter import count_tokens, compute_usage_percentage
from src.db.universe_db import list_universes_for_game, get_universe
from src.db.ruleset_db import get_ruleset

logging.getLogger().setLevel(logging.INFO)
MODEL_NAME = "gemini-2.0-flash"
CONTEXT_USAGE_THRESHOLD = 50.0

router = APIRouter()

summary_model = SentenceTransformer("all-MiniLM-L6-v2")

# Global conversation history storage per game instance.
conversation_histories: Dict[str, List[str]] = {}

# Track, per‐game, the latest news‐timestamp we've already included in a GM prompt
last_included_news_time: Dict[str, datetime] = {}

def build_compressed_context(game_id: str, gm_prompt: str, last_k: int = 20) -> str:
    """
    Returns a prompt string composed of:
      1) Universe metadata (name, description)
      2) Ruleset info (name, description, summary, long_summary)
      3) Current players in the game
      4) The opening scene (first GM message)
      5) The latest stored summary from game_history
      6) The last `last_k` chat messages
      7) The current user trigger (gm_prompt)
    """
    # 1) Universe & ruleset
    uni_section = ""
    ruleset_section = ""
    uni_ids = list_universes_for_game(game_id)
    if uni_ids:
        uni = get_universe(uni_ids[0])
        if uni:
            uni_section = f"Universe: {uni['name']} — {uni['description']}\n\n"
            rs = get_ruleset(uni.get("ruleset_id"))
            if rs:
                ruleset_section = (
                    f"Ruleset: {rs['name']} — {rs['description']}\n"
                    f"Summary: {rs.get('summary','')}\n\n"
                    f"Details: {rs.get('long_summary','')}\n\n"
                )

    # 2) Players list
    player_ids = list_players_in_game(game_id)
    names = []
    for cid in player_ids:
        char = get_character_by_id(cid)
        if char:
            names.append(char["name"])
    players_section = "Players: " + ", ".join(names) + "\n\n" if names else ""

    # 3) Opening scene (first GM message)
    opening_scene = ""
    for m in list_chat_messages(game_id):
        if m["sender"] == "GM":
            opening_scene = m["message"]
            break

    # 4) Latest stored summary
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT summary FROM game_history "
                "WHERE game_id=%s ORDER BY summary_date DESC LIMIT 1",
                (game_id,)
            )
            row = cur.fetchone()
        summary = row[0] if row else ""
    finally:
        conn.close()

    # 5) Recent messages
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sender, message FROM chat_messages "
                "WHERE game_id=%s ORDER BY timestamp DESC LIMIT %s",
                (game_id, last_k)
            )
            rows = cur.fetchall()
        rows.reverse()
        recent = "\n".join(f"{r[0]}: {r[1]}" for r in rows)
    finally:
        conn.close()

    # 6) Assemble compressed prompt
    return (
        f"{uni_section}"
        f"{ruleset_section}"
        f"{players_section}"
        f"Opening Scene:\n{opening_scene}\n\n"
        f"Summary of the Game So Far:\n{summary}\n\n"
        f"Recent Messages:\n{recent}\n\n"
        f"User (trigger): {gm_prompt}\n\n"
        "GM Response:"
    )

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

                    # Decide if any game mechanics should run before the GM response
                    full_history = "\n".join(conversation_histories[game_id])
                    tool_plan = plan_tool_calls(full_history, gm_prompt)

                    # Announce what tasks will run (if any)
                    planned = []
                    if isinstance(tool_plan, dict):
                        planned = [key for key in tool_plan.keys() if tool_plan.get(key)]
                    tasks_msg = (
                        "GM will run no additional tasks." if not planned
                        else f"GM will run tasks: {', '.join(planned)}"
                    )
                    game_db.save_chat_message(game_id, "System", tasks_msg)
                    conversation_histories[game_id].append(f"System: {tasks_msg}")
                    await manager.broadcast(game_id, json.dumps({
                        "game_id":   game_id,
                        "sender":    "System",
                        "message":   tasks_msg,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }))

                    dice_results = []
                    lore_chunks = []
                    lore_query = ""
                    if isinstance(tool_plan, dict) and tool_plan.get("dice"):
                        spec = tool_plan["dice"] or {}
                        num = int(spec.get("num_rolls", 1))
                        sides = int(spec.get("sides", 20))
                        dice_results = roll_dice(num, sides)
                        result_msg = f"Rolled {num}d{sides}: {dice_results}"
                        game_db.save_chat_message(game_id, "System", result_msg)
                        conversation_histories[game_id].append(f"System: {result_msg}")
                        await manager.broadcast(game_id, json.dumps({
                            "game_id":   game_id,
                            "sender":    "System",
                            "message":   result_msg,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        }))

                    if isinstance(tool_plan, dict) and tool_plan.get("lore"):
                        spec = tool_plan["lore"] or {}
                        lore_query = spec.get("query", "")
                        top_k = int(spec.get("top_k", 5))
                        if lore_query:
                            uni_ids = universe_db.list_universes_for_game(game_id)
                            if uni_ids:
                                uni = get_universe(uni_ids[0])
                                if uni and uni.get("ruleset_id"):
                                    lore_chunks = query_ruleset_chunks(uni["ruleset_id"], lore_query, top_k)

                    # ——— Build prompt, with 50%‐of‐context threshold ———
                    # count on the full history version (including any dice results)
                    full_history = "\n".join(conversation_histories[game_id])
                    lore_block = ""
                    if lore_chunks:
                        lore_lines = [f"Relevant Lore for '{lore_query}':"]
                        for idx, chunk in enumerate(lore_chunks, start=1):
                            lore_lines.append(f"{idx}. {chunk.strip()}")
                        lore_block = "\n".join(lore_lines) + "\n\n"

                    baseline_prompt = (
                        f"{news_block}"
                        f"{lore_block}"
                        f"Conversation History:\n{full_history}\n\n"
                        f"User (trigger): {gm_prompt}\n\n"
                        "GM Response:"
                    )
                    prompt_tokens = count_tokens(baseline_prompt, MODEL_NAME)
                    pct = compute_usage_percentage(prompt_tokens, MODEL_NAME)
                    logging.info(f"[TokenUsage] game={game_id} prompt={prompt_tokens} tokens ({pct:.1f}%)")

                    if pct >= CONTEXT_USAGE_THRESHOLD:
                        # compress
                        assembled_prompt = (
                            f"{news_block}"
                            f"{lore_block}"
                            + build_compressed_context(game_id, gm_prompt, last_k=20)
                        )
                    else:
                        assembled_prompt = baseline_prompt
                    # —————————————————————————————
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
                    
                    # Notify other players that the game advanced via /gm
                    notify_game_advanced(game_id, username)

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
