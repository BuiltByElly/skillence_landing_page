from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

from app.api.v1.dependencies import session_deps
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.models import Users
from app.schema.schema import UserCreate, UserJWT, UserLogin
from app.services.authentication import AuthService, get_current_user
from app.utils.set_cookies import set_cookies

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request,
    response: Response,
    form_data: UserCreate,
    db: session_deps,
):
    auth_service = AuthService(db)

    if await auth_service.validation_for_registration(form_data):
        user = await auth_service.register_user(form_data)

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(
            str(user.id), user.role, form_data.remember_me
        )

        # set cookies

        set_cookies(
            response,
            "refreshToken",
            refresh_token,
            60
            * 60
            * 24
            * (
                settings.REFRESH_TOKEN_EXPIRE_DAYS
                if form_data.remember_me
                else settings.REFRESH_TOKEN_EXPIRE_DAY
            ),
        )
        # write refresh token to db
        await auth_service.write_refresh_token_to_db(refresh_token, user)

        request.state.__setattr__("public_id", str(user.id))
        logger.info(f"User Action: user {user.id} registered")

        return {
            "success": True,
            "message": "Registered successfully",
            "accessToken": access_token,
        }
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="an error occurred while registering",
    )


@auth_router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    db: session_deps,
    form_data: UserLogin,
    response: Response,
):
    auth_service = AuthService(db)

    if await auth_service.validation_for_authentication(form_data):
        user = await auth_service.authenticate_user(form_data)
        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id), user.role)

        # set cookies
        set_cookies(
            response,
            "refreshToken",
            refresh_token,
            60
            * 60
            * 24
            * (
                settings.REFRESH_TOKEN_EXPIRE_DAYS
                if form_data.remember_me
                else settings.REFRESH_TOKEN_EXPIRE_DAY
            ),
        )
        # write refresh token to db
        await auth_service.write_refresh_token_to_db(refresh_token, user)

        request.state.__setattr__("public_id", str(user.id))
        logger.info(f"User Action: user {user.id} logged in")

        return {
            "success": True,
            "message": "Logged in successfully",
            "accessToken": access_token,
        }
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="an error occurred while registering",
    )


@auth_router.post("/refresh")
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    response: Response,
    db: session_deps,
    remember_me: bool = False,
):
    refresh_token = request.cookies.get("refreshToken")
    if not refresh_token:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")

    auth_service = AuthService(db)
    # Validate token type and decode
    payload = decode_token(refresh_token, token_type="refresh")
    user_jwt: UserJWT = UserJWT(sub=payload["sub"], role=payload["role"])

    try:
        await auth_service.validate_refresh_token(refresh_token)
        # generate new refresh and access token
        new_access_token = create_access_token(user_jwt.sub, user_jwt.role)
        new_refresh_token = create_refresh_token(
            user_jwt.sub, user_jwt.role, remember_me
        )
        dummy_user = Users(
            username="",
            password="",
            email="",
            role=user_jwt.role,
            id=UUID(user_jwt.sub),
        )
        await auth_service.write_refresh_token_to_db(
            new_refresh_token, dummy_user, remember_me
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Error refreshing token for user {user_jwt.sub}: {str(e)}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Failed to refresh token"
        )

    # set cookies
    set_cookies(
        response,
        "refreshToken",
        new_refresh_token,
        60
        * 60
        * 24
        * (
            settings.REFRESH_TOKEN_EXPIRE_DAYS
            if remember_me
            else settings.REFRESH_TOKEN_EXPIRE_DAY
        ),
    )

    logger.info(f"User Action: user {user_jwt.sub} refreshed token")

    return {
        "success": True,
        "message": "Token refreshed",
        "access_token": new_access_token,
    }


@auth_router.delete("/logout")
@limiter.limit("5/minute")
async def logout(
    response: Response,
    request: Request,
    current_user: Annotated[UserJWT, Depends(get_current_user)],
    db: session_deps,
):
    refresh_token = request.cookies.get("refreshToken")

    if not refresh_token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    response.delete_cookie(
        "refreshToken",
        secure=settings.is_prod,
        samesite="none" if settings.is_prod else "lax",
    )
    auth_service = AuthService(db)

    await auth_service.logout_user(refresh_token)

    logger.info(f"User Action: {current_user.sub} logged out")
    return {"success": True, "message": "Logged out successfully"}
