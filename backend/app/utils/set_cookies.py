from fastapi import Response

from app.core.config import settings


def set_cookies(response: Response, key: str, value: str, max_age: int):
    response.set_cookie(
        key,
        value,
        httponly=True,
        secure=settings.is_prod,
        samesite="none" if settings.is_prod else "lax",
        max_age=max_age,
    )
