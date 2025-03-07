document.addEventListener("DOMContentLoaded", () => {
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
      // After a successful login:
      document.getElementById("user-display").innerText = username;
      document.getElementById("login-form").style.display = "none";
      document.getElementById("lobby-interface").style.display = "block";

      // Load the user's characters into the dropdown.
      loadUserCharacters();
    } else {
      const error = await response.json();
      document.getElementById("login-error").innerText = error.detail || "Login failed";
    }
  });

  // Create Character button listener
  document.getElementById("create-character-button").addEventListener("click", async function() {
    console.log("Create Character button clicked.");
    const characterName = document.getElementById("character-name").value.trim();
    const characterClass = document.getElementById("character-class").value.trim() || "default";
    
    console.log("Character Name:", characterName);
    console.log("Character Class:", characterClass);

    if (!characterName) {
      document.getElementById("create-character-error").innerText = "Please enter a character name.";
      console.log("Character name missing.");
      return;
    }
    
    try {
      console.log("Sending POST request to /character/create");
      const response = await fetch("/character/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username,  // 'username' should be set on login
          name: characterName,
          character_class: characterClass
        })
      });
      
      console.log("Response received:", response);
      
      if (response.ok) {
        const newCharacter = await response.json();
        console.log("Character created successfully:", newCharacter);
        alert("Character created: " + newCharacter.name);
        // Clear the input fields after successful creation
        document.getElementById("character-name").value = "";
        document.getElementById("character-class").value = "default";
        document.getElementById("create-character-error").innerText = "";
        // Refresh the character dropdown list
        loadUserCharacters();
      } else {
        const error = await response.json();
        console.error("Error response:", error);
        document.getElementById("create-character-error").innerText = error.detail || "Failed to create character";
      }
    } catch (error) {
      console.error("Error creating character:", error);
      document.getElementById("create-character-error").innerText = "Error creating character";
    }
  });

  // Create new game button listener
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

  // Refresh game list button listener
  document.getElementById("refresh-games-button").addEventListener("click", async function() {
    const response = await fetch("/api/game/list");
    if (response.ok) {
      const data = await response.json();
      const gameListDiv = document.getElementById("game-list");
      gameListDiv.innerHTML = "";
      data.games.forEach(game => {
        const div = document.createElement("div");
        div.innerText = `ID: ${game.id}, Name: ${game.name}, Status: ${game.status}`;
        div.style.cursor = "pointer";
        // Highlight the game on hover for a better UX.
        div.addEventListener("mouseover", () => {
          div.style.backgroundColor = "#f0f0f0";
        });
        div.addEventListener("mouseout", () => {
          div.style.backgroundColor = "";
        });
        // Set the join-game-id field when the game entry is clicked.
        div.addEventListener("click", () => {
          document.getElementById("join-game-id").value = game.id;
          alert(`Selected game: ${game.name} (${game.id})`);
        });
        gameListDiv.appendChild(div);
      });
    }
  });

  // Join existing game button listener
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
    const characterSelect = document.getElementById("character-select");
    const selectedCharacterId = characterSelect.value;
    
    if (!selectedCharacterId) {
      alert("Please select your character before joining a game.");
      return;
    }
    
    characterId = selectedCharacterId; // Save the selected character id
    
    // Proceed with joining the game using the selected character ID.
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
	  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
	  ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/game/${currentGameId}/chat?character_id=${encodeURIComponent(characterId)}`);
	  
	  ws.onopen = function() {
		console.log("WebSocket connection opened.");
		document.getElementById("status").innerText = "Connected to game chat.";
	  };
	  
	  ws.onmessage = function(event) {
		console.log("Received message:", event.data);
		const msg = JSON.parse(event.data);
		const chatBox = document.getElementById("chat-box");
		const messageDiv = document.createElement("div");
		messageDiv.classList.add("message");
		messageDiv.innerHTML = `<strong>${msg.character_id}:</strong> ${msg.message} <span class="timestamp">[${new Date(msg.timestamp).toLocaleTimeString()}]</span>`;
		chatBox.appendChild(messageDiv);
		chatBox.scrollTop = chatBox.scrollHeight;
	  };
	  
	  ws.onclose = function() {
		console.log("WebSocket connection closed.");
		document.getElementById("status").innerText = "Disconnected from game chat.";
	  };
	  
	  ws.onerror = function(error) {
		console.error("WebSocket error:", error);
	  };
	}
	
  document.getElementById("send-button").addEventListener("click", function() {
  console.log("Send button event handler triggered.");
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) {
    console.warn("Message is empty.");
    return;
  }
  if (!ws) {
    console.warn("WebSocket object not defined.");
    return;
  }
  if (ws.readyState !== WebSocket.OPEN) {
    console.warn("WebSocket not open. Current readyState:", ws.readyState);
    return;
  }
  console.log("Sending message:", message);
  ws.send(message);
  input.value = "";
});

  // Function to load user characters into the dropdown
  async function loadUserCharacters() {
    try {
      const response = await fetch(`/character/list?username=${encodeURIComponent(username)}`);
      const characterSelect = document.getElementById("character-select");
      characterSelect.innerHTML = ""; // Clear any existing options

      if (response.ok) {
        const characters = await response.json();
        if (characters.length === 0) {
          const option = document.createElement("option");
          option.value = "";
          option.innerText = "No characters found. Please create one.";
          characterSelect.appendChild(option);
        } else {
          characters.forEach(character => {
            const option = document.createElement("option");
            option.value = character.id;
            option.innerText = character.name;
            characterSelect.appendChild(option);
          });
        }
      } else {
        console.error("Failed to load characters.");
        const option = document.createElement("option");
        option.value = "";
        option.innerText = "Error loading characters";
        characterSelect.appendChild(option);
      }
    } catch (error) {
      console.error("Error fetching characters:", error);
    }
  }
});
