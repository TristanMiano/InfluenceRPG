// src/server/static/js/chat.js
// Ensure universeId is passed into startChat to avoid undefined errors

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const username = params.get("username") || "";
  const gameId = params.get("game_id") || "";
  const characterId = params.get("character_id") || "";
  let universeId = params.get("universe_id");
  if (!universeId) {
    const hidden = document.getElementById("universe-id");
    universeId = hidden ? hidden.value : "";
  }

  document.getElementById("current-game-id").innerText = gameId;
  startChat(username, gameId, characterId, universeId);
});

function startChat(username, gameId, characterId, universeId) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl =
    `${protocol}//${window.location.host}/ws/game/${gameId}/chat?` +
    `username=${encodeURIComponent(username)}` +
    `&character_id=${encodeURIComponent(characterId)}`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    document.getElementById("status").innerText = "Connected to game chat.";
    if (universeId) {
      // initial load
      loadNews(universeId);
      loadConflicts(universeId);
      // refresh every 30 seconds
      setInterval(() => loadNews(universeId), 30 * 1000);
      setInterval(() => loadConflicts(universeId), 30 * 1000);
    }
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.innerHTML =
      `<strong>${msg.sender}:</strong> ${msg.message} ` +
      `<span class="timestamp">[${new Date(msg.timestamp).toLocaleTimeString()}]</span>`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  };

  ws.onclose = () => {
    document.getElementById("status").innerText = "Disconnected from game chat.";
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  document.getElementById("send-button").addEventListener("click", () => {
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (text && ws.readyState === WebSocket.OPEN) {
      ws.send(text);
      input.value = "";
    }
  });
}

async function loadNews(universeId) {
  try {
    const resp = await fetch(
      `/api/universe/${encodeURIComponent(universeId)}/news`
    );
    if (!resp.ok) return;
    const items = await resp.json();
    const box = document.getElementById("news-box");
    box.innerHTML = "";
    items.forEach((item) => {
      const div = document.createElement("div");
      div.innerHTML =
        `<em>[${new Date(item.published_at).toLocaleTimeString()}]</em> ${item.summary}`;
      box.appendChild(div);
    });
  } catch (e) {
    console.error("Error loading news:", e);
  }
}

async function loadConflicts(universeId) {
  try {
    const resp = await fetch(
      `/api/universe/${encodeURIComponent(universeId)}/conflicts`
    );
    if (!resp.ok) return;
    const items = await resp.json();
    const box = document.getElementById("conflict-box");
    box.innerHTML = "";
    if (items.length === 0) {
      box.innerHTML = "<em>No conflicts detected.</em>";
      return;
    }
    items.forEach((item) => {
      const div = document.createElement("div");
      div.classList.add("conflict-item");
      const info = item.conflict_info;
      div.innerHTML =
        `<strong>${new Date(item.detected_at).toLocaleTimeString()}</strong><br/>` +
        `${info.description || JSON.stringify(info)}<br/>` +
        `<em>Instances:</em> ${info.game_ids.join(", ")}`;
      box.appendChild(div);
    });
  } catch (e) {
    console.error("Error loading conflicts:", e);
  }
}
