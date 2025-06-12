// src/server/static/js/universe_create.js

async function loadRulesets() {
  try {
    const resp = await fetch("/api/ruleset/list");
    if (!resp.ok) throw new Error();
    const rulesets = await resp.json();
    const select = document.getElementById("ruleset-select");
    rulesets.forEach(rs => {
      const opt = document.createElement("option");
      opt.value = rs.id;
      opt.innerText = rs.name;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error("Error loading rulesets:", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadRulesets();

  const btn = document.getElementById("create-universe-button");
  const errorElem = document.getElementById("universe-create-error");
  const nameInput = document.getElementById("universe-name");
  const descInput = document.getElementById("universe-description");
  const select = document.getElementById("ruleset-select");

  btn.addEventListener("click", async () => {
    errorElem.innerText = "";
    const name = nameInput.value.trim();
    const description = descInput.value.trim();
    const rulesetId = select.value;

    if (!rulesetId) {
      errorElem.innerText = "Please select a ruleset.";
      return;
    }
    if (!name) {
      errorElem.innerText = "Please enter a universe name.";
      return;
    }

    try {
      const resp = await fetch("/api/universe/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, ruleset_id: rulesetId })
      });

      if (resp.ok) {
        // success → back to lobby (session retains username)
        window.location.href = "/lobby";
      } else {
        const err = await resp.json();
        errorElem.innerText = err.detail || "Universe creation failed.";
      }
    } catch (e) {
      console.error("Create universe error:", e);
      errorElem.innerText = "An error occurred.";
    }
  });
});
