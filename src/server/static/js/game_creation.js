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
  const params = new URLSearchParams(window.location.search);
  const username = document.getElementById("username").value;
  const universeSelect = document.getElementById("universe-select");
  const charSelect     = document.getElementById("character-select");

  loadAvailableCharacters(username);
  loadUniverses(params.get("universe_id"));

  const genBtn      = document.getElementById("generate-prompt-button");
  const regenBtn    = document.getElementById("regenerate-button");
  const createBtn   = document.getElementById("create-game-button");
  const promptBox   = document.getElementById("prompt-container");
  const promptField = document.getElementById("generated-prompt");
  const genError    = document.getElementById("generate-error");
  const createError = document.getElementById("create-error");

  async function fetchGeneratedPrompt() {
    genError.innerText = "";
    const universeId = universeSelect.value;
    const gameDesc   = document.getElementById("game-description").value.trim();
    if (!universeId) {
      genError.innerText = "Please select a universe.";
      return null;
    }
    if (!gameDesc) {
      genError.innerText = "Please enter a game description.";
      return null;
    }

    try {
      const resp = await fetch("/api/game/generate-setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ universe_id: universeId, game_description: gameDesc })
      });
      if (!resp.ok) {
        const err = await resp.json();
        genError.innerText = err.detail || "Failed to generate prompt.";
        return null;
      }
      const { generated_setup } = await resp.json();
	  return generated_setup;
    } catch (err) {
      console.error(err);
      genError.innerText = "Network error.";
      return null;
    }
  }

  genBtn.addEventListener("click", async () => {
    const prompt = await fetchGeneratedPrompt();
    if (prompt !== null) {
      promptField.value = prompt;
      promptBox.style.display = "block";
      createBtn.style.display = "block";
    }
  });

  regenBtn.addEventListener("click", async () => {
    const prompt = await fetchGeneratedPrompt();
    if (prompt !== null) {
      promptField.value = prompt;
    }
  });

  createBtn.addEventListener("click", async () => {
    createError.innerText = "";
    const gameName = document.getElementById("new-game-name").value.trim();
	const initialDetails = document.getElementById("game-description").value.trim();
    const charId   = charSelect.value;
    const universeId = universeSelect.value;
    const setupPrompt = promptField.value.trim();

    if (!gameName) {
      createError.innerText = "Please enter a game name.";
      return;
    }
    if (!charId) {
      createError.innerText = "Please select a character.";
      return;
    }
    if (!setupPrompt) {
      createError.innerText = "No prompt to submit. Please generate first.";
      return;
    }

    const payload = {
      name: gameName,
      character_id: charId,
      universe_id: universeId,
	  initial_details: initialDetails,
      setup_prompt: setupPrompt
    };

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
          `/chat?username=${encodeURIComponent(username)}` +
          `&game_id=${encodeURIComponent(gameId)}` +
          `&character_id=${encodeURIComponent(charId)}` +
          `&universe_id=${encodeURIComponent(universeId)}`;
      } else {
        const errorData = await resp.json();
		const detail = errorData.detail;
		if (Array.isArray(detail)) {
		  createError.innerText = detail.map(e => e.msg).join("; ");
		} else {
		  createError.innerText = String(detail);
		}
      }
    } catch (err) {
      console.error(err);
      createError.innerText = "Network error.";
    }
  });
});

