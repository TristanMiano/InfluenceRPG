// src/server/static/js/game_creation.js

// Load only characters that aren’t already in another active game
async function loadAvailableCharacters(username) {
  try {
    const resp = await fetch(
      `/character/list_available?username=${encodeURIComponent(username)}`
    );
    const select = document.getElementById("character-select");
    select.innerHTML = "";

    if (!resp.ok) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.innerText = "Error loading characters";
      select.appendChild(opt);
      return;
    }

    const chars = await resp.json();
    if (chars.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.innerText = "No available characters. Finish or leave your other game first.";
      select.appendChild(opt);
    } else {
      chars.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.innerText = c.name;
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Error loading characters:", err);
  }
}

// Load universes into the dropdown
async function loadUniverses(presetUniverse) {
  const select = document.getElementById("universe-select");
  try {
    const resp = await fetch("/api/universe/list");
    if (!resp.ok) {
      console.error("Failed to load universes");
      return;
    }
    const universes = await resp.json();
    universes.forEach(u => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.innerText = u.name;
      select.appendChild(opt);
    });
    if (presetUniverse) {
      select.value = presetUniverse;
    }
  } catch (err) {
    console.error("Error loading universes:", err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Read optional universe_id from URL
  const params = new URLSearchParams(window.location.search);
  const presetUniverse = params.get("universe_id");

  // Username from hidden input
  const username = document.getElementById("username").value;
  const universeSelect = document.getElementById("universe-select");

  // Populate character and universe selectors
  loadAvailableCharacters(username);
  loadUniverses(presetUniverse);

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

    // Build payload
    const payload = {
      name: gameName,
      initial_details: initialDetails,
      character_id: characterId
    };
    const universeId = universeSelect.value;
    if (universeId) payload.universe_id = universeId;

    try {
      const resp = await fetch("/api/game/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        const data = await resp.json();
        const gameId = data.id;
        window.location.href =
          `/chat?username=${encodeURIComponent(username)}&game_id=${encodeURIComponent(gameId)}&character_id=${encodeURIComponent(characterId)}`;
      } else {
        const err = await resp.json();
        errorElem.innerText = err.detail || "Game creation failed.";
      }
    } catch (err) {
      console.error("Game creation error:", err);
      errorElem.innerText = "An error occurred creating the game.";
    }
  });
});
