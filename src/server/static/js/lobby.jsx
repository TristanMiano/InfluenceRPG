// src/server/static/js/lobby.jsx

let selectedGameId = null;
let boundCharId = null;
let username = null;
let universeId = null;
let availableChars = [];

// Fetch any character already tied to this game (if any)
async function getBoundCharacter(gameId) {
  try {
    const resp = await fetch(
      `/api/game/${encodeURIComponent(gameId)}/character?username=${encodeURIComponent(username)}`
    );
    if (!resp.ok) return null;
    const { character_id } = await resp.json();
    return character_id;
  } catch (err) {
    console.error("Error checking bound character:", err);
    return null;
  }
}

// Load only available characters for joining new games
async function loadAvailableCharacters() {
  const select = document.getElementById("character-select");
  select.innerHTML = "";
  try {
    const resp = await fetch(
      `/character/list_available?username=${encodeURIComponent(username)}`
    );
    if (!resp.ok) throw new Error();
    const chars = await resp.json();
    availableChars = chars;
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
  } catch {
    const opt = document.createElement("option");
    opt.value = "";
    opt.innerText = "Error loading characters";
    availableChars = [];
    select.appendChild(opt);
  }
}

// Populate and handle game list
async function refreshGames() {
  const listDiv = document.getElementById("game-list");
  listDiv.innerHTML = "";
  try {
    const resp = await fetch("/api/game/list");
    if (!resp.ok) throw new Error();
    const { games } = await resp.json();

    for (const game of games) {
      // figure out your relation to this game
      const joinedId = await getBoundCharacter(game.id);

      // decide which badges to show
      const badges = [];
      if (joinedId) {
        badges.push({ text: "Joined",      cls: "status-joined" });
      } else if (availableChars.length === 0) {
        badges.push({ text: "No characters", cls: "status-none" });
      } else if (game.status === "waiting") {
        badges.push({ text: "Joinable",    cls: "status-joinable" });
      } else if (game.status === "active") {
        badges.push({ text: "Active",      cls: "status-active" });
      } else {
        badges.push({ text: game.status.charAt(0).toUpperCase() + game.status.slice(1), cls: `status-${game.status}` });
        badges.push({ text: "Closed",      cls: "status-closed" });
      }

      // build the line
      const div = document.createElement("div");
      div.style.cursor = "pointer";
      let html = `ID: ${game.id}, Name: ${game.name}`;
      badges.forEach(b => {
        html += ` <span class="status-badge ${b.cls}">${b.text}</span>`;
      });
      div.innerHTML = html;

      div.addEventListener("mouseover", () => div.style.backgroundColor = "#f0f0f0");
      div.addEventListener("mouseout", () => div.style.backgroundColor = "");

      div.addEventListener("click", async () => {
        selectedGameId = game.id;
        boundCharId = await getBoundCharacter(game.id);

        const charSelect = document.getElementById("character-select");
        const errorElem  = document.getElementById("join-game-error");
        const joinBtn    = document.getElementById("join-game-button");

        // Update UI based on whether user has already joined
        if (boundCharId) {
          charSelect.style.display = "none";
          errorElem.innerText    = "You’re already in this game — click below to rejoin.";
          joinBtn.textContent    = "Rejoin Game";
        } else {
          charSelect.style.display = "";
          errorElem.innerText    = "";
          joinBtn.textContent    = "Join Game";
        }
      });

      listDiv.appendChild(div);
    }
  } catch (err) {
    console.error("Error fetching game list:", err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const params     = new URLSearchParams(window.location.search);
  username         = params.get("username")    || "";
  universeId       = params.get("universe_id") || "";

  document.getElementById("user-display").innerText = username;
  loadAvailableCharacters().then(() => refreshGames());

  document.getElementById("refresh-games-button").addEventListener("click", refreshGames);

  document.getElementById("join-game-button").addEventListener("click", async () => {
    const errorElem = document.getElementById("join-game-error");
    errorElem.innerText = "";

    if (!selectedGameId) {
      errorElem.innerText = "Please select a game first.";
      return;
    }

    // Rejoin existing
    if (boundCharId) {
      let url = `/chat?username=${encodeURIComponent(username)}`
              + `&game_id=${encodeURIComponent(selectedGameId)}`
              + `&character_id=${encodeURIComponent(boundCharId)}`;
      if (universeId) url += `&universe_id=${encodeURIComponent(universeId)}`;
      window.location.href = url;
      return;
    }

    // New join flow
    const charSelect = document.getElementById("character-select");
    const characterId = charSelect.value;
    if (!characterId) {
      errorElem.innerText = "Please select a character.";
      return;
    }

    try {
      const resp = await fetch(
        `/api/game/${encodeURIComponent(selectedGameId)}/join`,
        {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ character_id: characterId, username })
        }
      );

      if (resp.ok) {
        let url = `/chat?username=${encodeURIComponent(username)}`
                + `&game_id=${encodeURIComponent(selectedGameId)}`
                + `&character_id=${encodeURIComponent(characterId)}`;
        if (universeId) url += `&universe_id=${encodeURIComponent(universeId)}`;
        window.location.href = url;
      } else {
        const errData = await resp.json();
        errorElem.innerText = errData.detail || "Could not join game.";
      }
    } catch (err) {
      console.error("Join game error:", err);
      errorElem.innerText = "An error occurred joining the game.";
    }
  });
});
