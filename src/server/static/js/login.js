document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const loginButton = document.getElementById("login-button");
  const errorElem = document.getElementById("login-error");

  loginButton.addEventListener("click", async function(event) {
    event.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
      errorElem.innerText = "Please enter both username and password.";
      return;
    }

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        // Redirect to lobby, passing username
        window.location.href = `/lobby`;
      } else {
        const errorData = await response.json();
        errorElem.innerText = errorData.detail || "Login failed";
      }
    } catch (err) {
      console.error("Login error:", err);
      errorElem.innerText = "An error occurred during login.";
    }
  });
});