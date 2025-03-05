let ws;
let username = "";
let currentGameId = "";
let characterId = "";

// Login process
document.getElementById("login-button").addEventListener("click", async function() {
username = document.getElementById("username").value.trim();
const password = document.getElementById("password").value;

if (!username || !password) {
  document.getElementById("login-error").innerText = "Please enter both username and password.";
  return;
}

const response = await fetch("/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password })
});

if (response.ok) {
  const data = await response.json();
  console.log("Login successful:", data);
  document.getElementById("user-display").innerText = username;
  document.getElementById("login-form").style.display = "none";
  document.getElementById("lobby-interface").style.display = "block";
} else {
  const error = await response.json();
  document.getElementById("login-error").innerText = error.detail || "Login failed";
}
});

// Create new game
document.getElementById("create-game-button").addEventListener("click", async function() {
const gameName = document.getElementById("new-game-name").value.trim();
if (!gameName) {
  document.getElementById("create-game-error").innerText = "Please enter a game name.";
  return;
}

const response = await fetch("/api/game/create", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: gameName })
});

if (response.ok) {
  const data = await response.json();
  console.log("Game created:", data);
  currentGameId = data.id;
  document.getElementById("current-game-id").innerText = currentGameId;
  joinGameLobby();
} else {
  const error = await response.json();
  document.getElementById("create-game-error").innerText = error.detail || "Game creation failed";
}
});

// Refresh game list
document.getElementById("refresh-games-button").addEventListener("click", async function() {
const response = await fetch("/api/game/list");
if (response.ok) {
  const data = await response.json();
  const gameListDiv = document.getElementById("game-list");
  gameListDiv.innerHTML = "";
  data.games.forEach(game => {
	const div = document.createElement("div");
	div.innerText = `ID: ${game.id}, Name: ${game.name}, Status: ${game.status}`;
	gameListDiv.appendChild(div);
  });
}
});

// Join existing game
document.getElementById("join-game-button").addEventListener("click", async function() {
currentGameId = document.getElementById("join-game-id").value.trim();
if (!currentGameId) {
  document.getElementById("join-game-error").innerText = "Please enter a game ID.";
  return;
}
joinGameLobby();
});

// Function to join game lobby (register character and show chat)
async function joinGameLobby() {
characterId = document.getElementById("character-id").value.trim();
if (!characterId) {
  alert("Please enter your Character ID before joining a game.");
  return;
}

// Call join game endpoint
const response = await fetch(`/api/game/${currentGameId}/join`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ character_id: characterId })
});

if (response.ok) {
  const data = await response.json();
  console.log("Joined game:", data);
  document.getElementById("lobby-interface").style.display = "none";
  document.getElementById("chat-interface").style.display = "block";
  document.getElementById("current-game-id").innerText = currentGameId;
  startChat();
} else {
  const error = await response.json();
  document.getElementById("join-game-error").innerText = error.detail || "Failed to join game";
}
}

// Chat functionality
function startChat() {
ws = new WebSocket(`ws://${window.location.host}/ws/game/${currentGameId}/chat?character_id=${encodeURIComponent(characterId)}`);

ws.onopen = function() {
  document.getElementById("status").innerText = "Connected to game chat.";
};

ws.onmessage = function(event) {
  const msg = JSON.parse(event.data);
  const chatBox = document.getElementById("chat-box");
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message");
  messageDiv.innerHTML = `<strong>${msg.character_id}:</strong> ${msg.message} <span class="timestamp">[${new Date(msg.timestamp).toLocaleTimeString()}]</span>`;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
};

ws.onclose = function() {
  document.getElementById("status").innerText = "Disconnected from game chat.";
};
}

document.getElementById("send-button").addEventListener("click", function() {
const input = document.getElementById("chat-input");
const message = input.value.trim();
if (message && ws && ws.readyState === WebSocket.OPEN) {
  ws.send(message);
  input.value = "";
}
});

// Send message on Enter key press
document.getElementById("chat-input").addEventListener("keyup", function(event) {
if (event.key === "Enter") {
  document.getElementById("send-button").click();
}
});