// src/server/static/js/lobby.jsx

let selectedGameId = null;
let boundCharId = null;
let universeId = null;
let availableChars = [];
let notifications = [];
let currentMessages = [];

async function loadUniverses() {
  const select = document.getElementById("universe-filter");
  select.innerHTML = "";
  const optAll = document.createElement("option");
  optAll.value = "";
  optAll.innerText = "All Universes";
  select.appendChild(optAll);
  try {
    const resp = await fetch('/api/universe/list');
    if (!resp.ok) throw new Error();
    const universes = await resp.json();
    universes.forEach(u => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.innerText = u.name;
      select.appendChild(opt);
    });
  } catch {
    const err = document.createElement("option");
    err.value = "";
    err.innerText = "Error loading universes";
    select.appendChild(err);
  }
}

async function loadNotifications() {
  try {
    const resp = await fetch('/api/notifications');
    if (!resp.ok) return;
    const data = await resp.json();
    notifications = data.notifications || [];
    const countElem = document.getElementById('notification-count');
    const unread = notifications.filter(n => !n.read).length;
    countElem.textContent = unread > 0 ? unread : '';
    const panel = document.getElementById('notification-panel');
    panel.innerHTML = '';
    if (notifications.length === 0) {
      panel.innerHTML = '<em>No notifications</em>';
    } else {
      const list = document.createElement('ul');
      notifications.forEach(n => {
        const li = document.createElement('li');
        li.textContent = n.message;
        list.appendChild(li);
      });
      panel.appendChild(list);
    }
  } catch (err) {
    console.error('Error loading notifications:', err);
  }
}

async function loadMessageCount() {
  try {
    const resp = await fetch('/api/messages/unread_count');
    if (!resp.ok) return;
    const data = await resp.json();
    const countElem = document.getElementById('messages-count');
    countElem.textContent = data.unread > 0 ? data.unread : '';
  } catch (err) {
    console.error('Error loading message count:', err);
  }
}

async function loadMessages(withUser) {
  if (!withUser) return;
  try {
    const resp = await fetch(`/api/messages?user=${encodeURIComponent(withUser)}`);
    if (!resp.ok) return;
    const data = await resp.json();
    currentMessages = data.messages || [];
    const list = document.getElementById('message-list');
    list.innerHTML = '';
    currentMessages.forEach(m => {
      const div = document.createElement('div');
      div.textContent = `${m.sender}: ${m.message}`;
      list.appendChild(div);
    });
  } catch (err) {
    console.error('Error loading messages:', err);
  }
}

async function markMessagesRead(withUser) {
  if (!withUser) return;
  try {
    await fetch('/api/messages/mark_read', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: withUser })
    });
  } catch (err) {
    console.error('Error marking messages read:', err);
  }
}

async function sendMessage(recipient, text) {
  try {
    await fetch('/api/messages/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient, message: text })
    });
  } catch (err) {
    console.error('Error sending message:', err);
  }
}

// Fetch any character already tied to this game (if any)
async function getBoundCharacter(gameId) {
  try {
    const resp = await fetch(
      `/api/game/${encodeURIComponent(gameId)}/character`
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
      `/character/list_available`
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
    const search = document.getElementById("search-games-input").value.trim();
    const uniFilter = document.getElementById("universe-filter").value;
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (uniFilter) params.set("universe_id", uniFilter);
    const resp = await fetch(`/api/game/list?${params.toString()}`);
    if (!resp.ok) throw new Error();
    const { games } = await resp.json();

    for (const game of games) {
      const joinedId = await getBoundCharacter(game.id);

      const badges = [];

      // Always show the game's current status
      if (game.status === "waiting") {
        badges.push({ text: "Waiting", cls: "status-waiting" });
      } else if (game.status === "active") {
        badges.push({ text: "Active", cls: "status-active" });
      } else if (game.status === "closed") {
        badges.push({ text: "Closed", cls: "status-closed" });
      } else if (game.status === "merged") {
        badges.push({ text: "Merged", cls: "status-merged" });
        // merged games are also closed
        badges.push({ text: "Closed", cls: "status-closed" });
      } else if (game.status === "branched") {
        badges.push({ text: "Branched", cls: "status-branched" });
        badges.push({ text: "Closed", cls: "status-closed" });
      } else {
        badges.push({ text: game.status.charAt(0).toUpperCase() + game.status.slice(1), cls: `status-${game.status}` });
      }

      // User-specific statuses - show all that apply
      if (joinedId) {
        badges.push({ text: "Joined", cls: "status-joined" });
      }
      if (availableChars.length === 0) {
        badges.push({ text: "No characters", cls: "status-none" });
      }
      if (!joinedId && availableChars.length > 0 && game.status === "waiting") {
        badges.push({ text: "Joinable", cls: "status-joinable" });
      }

      const div = document.createElement("div");
      div.style.cursor = "pointer";
      let html = `Name: ${game.name}`;
      if (game.universe_names && game.universe_names.length > 0) {
        html += ` – ${game.universe_names.join(', ')}`;
      }
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
        const errorElem = document.getElementById("join-game-error");
        const joinBtn = document.getElementById("join-game-button");

        if (boundCharId) {
          charSelect.style.display = "none";
          errorElem.innerText = "You’re already in this game — click below to rejoin.";
          joinBtn.textContent = "Rejoin Game";
        } else {
          charSelect.style.display = "";
          errorElem.innerText = "";
          joinBtn.textContent = "Join Game";
        }
      });

      listDiv.appendChild(div);
    }
  } catch (err) {
    console.error("Error fetching game list:", err);
  }
}

// Page setup
document.addEventListener("DOMContentLoaded", () => {
  // Read username & universeId from hidden inputs
  const username = document.getElementById("username").value;
  universeId = document.getElementById("universe-id").value;

  // Set welcome text
  document.getElementById("user-display").innerText = username;

  // Hamburger menu elements
  const btn = document.getElementById('menu-button');
  const menu = document.getElementById('dropdown-menu');
  if (btn && menu) {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      menu.classList.toggle('show');
    });
    document.addEventListener('click', () => menu.classList.remove('show'));
    menu.addEventListener('click', e => e.stopPropagation());
  }
  
  // Notification bell
  const notifBtn = document.getElementById('notification-button');
  const notifPanel = document.getElementById('notification-panel');
  if (notifBtn && notifPanel) {
    notifBtn.addEventListener('click', async e => {
      e.stopPropagation();
      notifPanel.classList.toggle('show');
      await fetch('/api/notifications/mark_read', { method: 'POST' });
      loadNotifications();
    });
    document.addEventListener('click', () => notifPanel.classList.remove('show'));
    notifPanel.addEventListener('click', e => e.stopPropagation());
  }
  
  // Messages icon
  const msgBtn = document.getElementById('message-button');
  if (msgBtn) {
    msgBtn.addEventListener('click', () => {
      window.location.href = '/messages';
    });
  }

  loadNotifications();
  loadMessageCount();


  // Load universes, characters & games
  loadUniverses().then(() => {
    loadAvailableCharacters().then(() => refreshGames());
  });

  document.getElementById("search-games-input").addEventListener("input", refreshGames);
  document.getElementById("universe-filter").addEventListener("change", refreshGames);

  document.getElementById("refresh-games-button").addEventListener("click", refreshGames);

  document.getElementById("join-game-button").addEventListener("click", async () => {
    const errorElem = document.getElementById("join-game-error");
    errorElem.innerText = "";

    if (!selectedGameId) {
      errorElem.innerText = "Please select a game first.";
      return;
    }

    if (boundCharId) {
      let url = `/chat?game_id=${encodeURIComponent(selectedGameId)}`
              + `&character_id=${encodeURIComponent(boundCharId)}`;
      if (universeId) url += `&universe_id=${encodeURIComponent(universeId)}`;
      window.location.href = url;
      return;
    }

    const charSelect = document.getElementById("character-select");
    const characterId = charSelect.value;
    if (!characterId) {
      errorElem.innerText = "Please select a character.";
      return;
    }

    try {
      const resp = await fetch(
        `/api/game/${encodeURIComponent(selectedGameId)}/join`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ character_id: characterId }) }
      );

      if (resp.ok) {
        let url = `/chat?game_id=${encodeURIComponent(selectedGameId)}`
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
