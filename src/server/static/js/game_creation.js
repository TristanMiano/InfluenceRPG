// src/server/static/js/game_creation.js

// Helper: Load characters for the given username into the select dropdown
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
        opt.innerText = "No characters found. Please create one first.";
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

// Initialize page
document.addEventListener("DOMContentLoaded", () => {
  const username = document.getElementById("username").value;
  loadUserCharacters(username);

  document.getElementById("create-game-button").addEventListener("click", async () => {
    const gameName = document.getElementById("new-game-name").value.trim();
    const initialDetails = document.getElementById("initial-details").value.trim();
    const characterId = document.getElementById("character-select").value;
    const errorElem = document.getElementById("create-game-error");
    errorElem.innerText = "";

    if (!gameName) {
      errorElem.innerText = "Please enter a game name.";
      return;
    }
    if (!characterId) {
      errorElem.innerText = "Please select a character.";
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
        window.location.href = 
          `/chat?username=${encodeURIComponent(username)}&game_id=${encodeURIComponent(gameId)}&character_id=${encodeURIComponent(characterId)}`;
      } else {
        const err = await response.json();
        errorElem.innerText = err.detail || "Game creation failed.";
      }
    } catch (err) {
      console.error("Game creation error:", err);
      errorElem.innerText = "An error occurred creating the game.";
    }
  });
});