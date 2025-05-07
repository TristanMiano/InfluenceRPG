document.addEventListener("DOMContentLoaded", () => {
  // Extract username from query params
  const params = new URLSearchParams(window.location.search);
  const username = params.get("username") || "";

  // Display username
  const userDisplay = document.getElementById("user-display");
  if (userDisplay) userDisplay.innerText = username;

  // Load user's characters
  loadUserCharacters(username);

  // Character creation
  document.getElementById("create-character-button").addEventListener("click", async () => {
    const nameInput = document.getElementById("character-name");
    const classInput = document.getElementById("character-class");
    const errorElem = document.getElementById("create-character-error");

    const characterName = nameInput.value.trim();
    const characterClass = classInput.value.trim() || "default";

    if (!characterName) {
      errorElem.innerText = "Please enter a character name.";
      return;
    }

    try {
      const response = await fetch("/character/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, name: characterName, character_class: characterClass })
      });

      if (response.ok) {
        const newChar = await response.json();
        alert("Character created: " + newChar.name);
        nameInput.value = "";
        classInput.value = "default";
        errorElem.innerText = "";
        loadUserCharacters(username);
      } else {
        const err = await response.json();
        errorElem.innerText = err.detail || "Failed to create character";
      }
    } catch (err) {
      console.error("Character creation error:", err);
      errorElem.innerText = "Error creating character.";
    }
  });

  // Game creation
  document.getElementById("create-game-button").addEventListener("click", async () => {
    const nameInput = document.getElementById("new-game-name");
    const detailsInput = document.getElementById("initial-details");
    const errorElem = document.getElementById("create-game-error");

    const gameName = nameInput.value.trim();
    const initialDetails = detailsInput.value.trim();

    if (!gameName) {
      errorElem.innerText = "Please enter a game name.";
      return;
    }

    try {
      const response = await fetch("/api/game/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: gameName, initial_details: initialDetails })
      });

      if (response.ok) {
        const data = await response.json();
        const gameId = data.id;
        window.location.href = `/chat?username=${encodeURIComponent(username)}&game_id=${encodeURIComponent(gameId)}&character_id=${encodeURIComponent(document.getElementById("character-select").value)}`;
      } else {
        const err = await response.json();
        errorElem.innerText = err.detail || "Game creation failed";
      }
    } catch (err) {
      console.error("Game creation error:", err);
      errorElem.innerText = "Error creating game.";
    }
  });

  // Refresh games list
  document.getElementById("refresh-games-button").addEventListener("click", refreshGames);

  // Join game button
  document.getElementById("join-game-button").addEventListener("click", () => {
    const gameIdInput = document.getElementById("join-game-id");
    const errorElem = document.getElementById("join-game-error");
    const selectedChar = document.getElementById("character-select").value;

    const gameId = gameIdInput.value.trim();
    if (!gameId) {
      errorElem.innerText = "Please enter a game ID.";
      return;
    }

    window.location.href = `/chat?username=${encodeURIComponent(username)}&game_id=${encodeURIComponent(gameId)}&character_id=${encodeURIComponent(selectedChar)}`;
  });

  // Initial load of games
  refreshGames();
});

async function loadUserCharacters(username) {
  try {
    const response = await fetch(`/character/list?username=${encodeURIComponent(username)}`);
    const select = document.getElementById("character-select");
    select.innerHTML = "";

    if (response.ok) {
      const chars = await response.json();
      if (chars.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.innerText = "No characters found. Please create one.";
        select.appendChild(opt);
      } else {
        chars.forEach(c => {
          const opt = document.createElement("option");
          opt.value = c.id;
          opt.innerText = c.name;
          select.appendChild(opt);
        });
      }
    } else {
      const opt = document.createElement("option");
      opt.value = "";
      opt.innerText = "Error loading characters";
      select.appendChild(opt);
    }
  } catch (err) {
    console.error("Error loading characters:", err);
  }
}

async function refreshGames() {
  try {
    const response = await fetch("/api/game/list");
    if (response.ok) {
      const data = await response.json();
      const listDiv = document.getElementById("game-list");
      listDiv.innerHTML = "";

      data.games.forEach(game => {
        const div = document.createElement("div");
        div.innerText = `ID: ${game.id}, Name: ${game.name}, Status: ${game.status}`;
        div.style.cursor = "pointer";
        div.addEventListener("mouseover", () => div.style.backgroundColor = "#f0f0f0");
        div.addEventListener("mouseout", () => div.style.backgroundColor = "");
        div.addEventListener("click", () => document.getElementById("join-game-id").value = game.id);
        listDiv.appendChild(div);
      });
    }
  } catch (err) {
    console.error("Error fetching game list:", err);
  }
}
