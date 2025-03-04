# src/models/user.py
from pydantic import BaseModel

class User(BaseModel):
    username: str
    role: str
