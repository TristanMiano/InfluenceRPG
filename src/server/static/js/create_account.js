document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  const errorElem = document.querySelector(".error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const password2 = document.getElementById("password2").value;

    if (!username || !password || !password2) {
      errorElem.innerText = "All fields are required.";
      return;
    }
    if (password !== password2) {
      errorElem.innerText = "Passwords do not match.";
      return;
    }

    try {
      const resp = await fetch("/create-account", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password, password2 })
      });

      if (resp.redirected) {
        // On success, form handler redirects back to login
        window.location.href = resp.url;
      } else if (!resp.ok) {
        const text = await resp.text();
        errorElem.innerText = text || "Account creation failed.";
      }
    } catch (err) {
      console.error("Create account error:", err);
      errorElem.innerText = "An error occurred.";
    }
  });
});