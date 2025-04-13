import pytest
from fastapi.testclient import TestClient
from src.server.main import app

# Define a fake authenticate_user function to simulate database responses.
def fake_authenticate_user(username: str, password: str):
    # For our tests, only the credentials below are considered valid.
    if username == "testuser" and password == "correctpassword":
        return {"username": username, "hashed_password": "fake_hash", "role": "player"}
    return None

# Use a pytest fixture to override the authenticate_user function in the auth module.
@pytest.fixture(autouse=True)
def override_authenticate_user(monkeypatch):
    # Import the auth module from src.auth and override its authenticate_user function.
    from src.auth import auth
    monkeypatch.setattr(auth, "authenticate_user", fake_authenticate_user)
    yield

# Initialize the TestClient with our FastAPI app.
client = TestClient(app)

def test_successful_login():
    """
    Test that a POST request to /login with valid credentials returns a success response.
    """
    response = client.post("/login", json={
        "username": "testuser",
        "password": "correctpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "player"
    assert "Login successful" in data["message"]

def test_invalid_login():
    """
    Test that a POST request to /login with invalid credentials returns a 401 Unauthorized error.
    """
    response = client.post("/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.json()
    # The error response from our login endpoint returns a "detail" key.
    assert data["detail"] == "Invalid credentials"

def test_login_validation_error():
    """
    Test that a POST request to /login with missing required fields returns a 422 Unprocessable Entity error.
    """
    # Omit the "password" key to trigger validation errors.
    response = client.post("/login", json={
        "username": "testuser"
    })
    assert response.status_code == 422
