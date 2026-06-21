import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.config import settings
from app.models.models import UserRole

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password=password, hash=hashed_password)


def hash_refresh_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str, user_role: UserRole):
    return jwt.encode(
        {
            "sub": user_id,
            "role": user_role,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "type": "access",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(user_id: str, user_role: UserRole, remember_me: bool = False):
    return jwt.encode(
        {
            "sub": user_id,
            "role": user_role,
            "exp": datetime.now(timezone.utc)
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                if remember_me
                else settings.REFRESH_TOKEN_EXPIRE_DAY
            ),
            "type": "refresh",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str, token_type: str | None = None):
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token error"
        )

    if token_type and decoded_token.get("type") != token_type:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    return decoded_token
