# src/auth/auth.py
from src.utils.security import hash_password, verify_password

# In-memory user database for prototype purposes.
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),  # Prototype password; replace in production.
        "role": "admin"
    },
    "player1": {
        "username": "player1",
        "hashed_password": hash_password("player123"),
        "role": "player"
    }
}

def authenticate_user(username: str, password: str):
    """
    Authenticate the user by username and password.

    Args:
        username: The username as a string.
        password: The plain text password as a string.

    Returns:
        A dictionary containing user details if credentials are valid; otherwise, None.
    """
    user = users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
