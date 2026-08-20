"""
Low-level security primitives: password verification and JWT create/decode.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.hash import bcrypt

from app.core.config import settings


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.verify(plain_password, password_hash)


def create_access_token(*, user_id: str, role: str, profile_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "profile_id": profile_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None