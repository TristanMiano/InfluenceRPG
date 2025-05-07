document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const username = params.get("username") || "";
  const gameId = params.get("game_id") || "";
  const characterId = params.get("character_id") || "";

  document.getElementById("current-game-id").innerText = gameId;
  startChat(username, gameId, characterId);
});

function startChat(username, gameId, characterId) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(
    `${protocol}//${window.location.host}/ws/game/${gameId}/chat?username=${encodeURIComponent(username)}&character_id=${encodeURIComponent(characterId)}`
  );

  ws.onopen = () => {
    document.getElementById("status").innerText = "Connected to game chat.";
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.innerHTML = `<strong>${msg.sender}:</strong> ${msg.message} <span class="timestamp">[${new Date(msg.timestamp).toLocaleTimeString()}]</span>`;
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
