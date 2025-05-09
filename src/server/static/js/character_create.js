document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("char-create-form");
  form.addEventListener("submit", async e => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const name = document.getElementById("name").value.trim();
    const character_class = document.getElementById("character_class").value;

    // Gather attributes into an object
    const character_data = {};
    ["Stature","Charisma","Tactics","Gravitas","Resolve","Ingenuity"]
      .forEach(attr => {
        character_data[attr] = parseInt(document.getElementById(attr).value, 10);
      });

    const payload = { username, name, character_class, character_data };

    try {
      const resp = await fetch("/character/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        // Back to lobby once done
        window.location.href = `/lobby?username=${encodeURIComponent(username)}`;
      } else {
        const err = await resp.json();
        document.getElementById("error").innerText = err.detail || "Failed to create character";
      }
    } catch (err) {
      console.error(err);
      document.getElementById("error").innerText = "Error creating character.";
    }
  });
});
