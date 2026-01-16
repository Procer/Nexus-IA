from app.core.security import create_access_token, decode_token, verify_password, get_password_hash
import pytest
from datetime import timedelta

def test_password_hashing():
    password = "secret"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_token():
    data = {"sub": "testuser", "client_id": 123}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == "testuser"
    assert decoded["client_id"] == 123
