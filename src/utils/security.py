# src/utils/security.py
import hashlib

def hash_password(password: str) -> str:
    """Return a SHA256 hash of the given password."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the hash of the plain_password matches the hashed_password."""
    return hash_password(plain_password) == hashed_password
