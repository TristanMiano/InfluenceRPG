// src/server/static/js/chat.js
// Use session-injected username rather than URL param

document.addEventListener("DOMContentLoaded", () => {
  // Read username from hidden input
  const userElem = document.getElementById("username");
  const username = userElem ? userElem.value : "";

  const params = new URLSearchParams(window.location.search);
  const gameId = params.get("game_id") || "";
  const characterId = params.get("character_id") || "";

  // Universe ID: prefer URL, fallback to hidden input
  let universeId = params.get("universe_id");
  if (!universeId) {
    const hidden = document.getElementById("universe-id");
    universeId = hidden ? hidden.value : "";
  }

  document.getElementById("current-game-id").innerText = gameId;
  startChat(username, gameId, characterId, universeId);
});

async function startChat(username, gameId, characterId, universeId) {
  const gameResp = await fetch(`/api/game/${encodeURIComponent(gameId)}`);
  if (!gameResp.ok) return;
  const game = await gameResp.json();
  if (game.status === "closed" || game.status === "merged") {
    document.getElementById("status").innerText = "Game closed – chat disconnected.";
    await loadPastMessages(gameId);
    if (universeId) {
      loadNews(universeId);
      loadConflicts(universeId);
    }
    return;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl =
    `${protocol}//${window.location.host}/ws/game/${gameId}/chat?` +
    `username=${encodeURIComponent(username)}` +
    `&character_id=${encodeURIComponent(characterId)}`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    document.getElementById("status").innerText = "Connected to game chat.";
    if (universeId) {
      loadNews(universeId);
      loadConflicts(universeId);
      setInterval(() => loadNews(universeId), 30 * 1000);
      setInterval(() => loadConflicts(universeId), 30 * 1000);
    }
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const chatBox = document.getElementById("chat-box");

    const rawHtml = marked.parse(msg.message);
    const safeHtml = DOMPurify.sanitize(rawHtml);

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.innerHTML =
      `<strong>${msg.sender}:</strong> ${safeHtml} ` +
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

  document.querySelectorAll(".gm-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cmd = btn.getAttribute("data-command");
      if (cmd && ws.readyState === WebSocket.OPEN) {
        ws.send(cmd);
      }
    });
  });
}

async function loadPastMessages(gameId) {
  try {
    const resp = await fetch(`/api/game/${encodeURIComponent(gameId)}/messages`);
    if (!resp.ok) return;
    const data = await resp.json();
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = "";
    data.messages.forEach((msg) => {
      const raw = marked.parse(msg.message);
      const safe = DOMPurify.sanitize(raw);
      const div = document.createElement("div");
      div.classList.add("message");
      div.innerHTML =
        `<strong>${msg.sender}:</strong> ${safe} ` +
        `<span class="timestamp">[${new Date(msg.timestamp).toLocaleTimeString()}]</span>`;
      chatBox.appendChild(div);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (e) {
    console.error("Error loading messages:", e);
  }
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
