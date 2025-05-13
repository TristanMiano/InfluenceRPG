document.addEventListener("DOMContentLoaded", () => {
  const username = document.getElementById("username").value;
  const nameInput = document.getElementById("universe-name");
  const descInput = document.getElementById("universe-description");
  const errorElem = document.getElementById("universe-create-error");
  const btn = document.getElementById("create-universe-button");

  btn.addEventListener("click", async () => {
    errorElem.innerText = "";
    const name = nameInput.value.trim();
    const description = descInput.value.trim();

    if (!name) {
      errorElem.innerText = "Please enter a universe name.";
      return;
    }

    try {
      const resp = await fetch("/api/universe/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description })
      });

      if (resp.ok) {
        const data = await resp.json();
        // Redirect into the new-universe–prefilled game creation form
        window.location.href = `/game/new?username=${encodeURIComponent(username)}&universe_id=${encodeURIComponent(data.id)}`;
      } else {
        const err = await resp.json();
        errorElem.innerText = err.detail || "Creation failed.";
      }
    } catch (e) {
      console.error(e);
      errorElem.innerText = "An error occurred.";
    }
  });
});
