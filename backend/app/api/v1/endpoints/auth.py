from fastapi import APIRouter, HTTPException, Request, Response
from loguru import logger
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.v1.dependencies import session_deps
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, create_refresh_token
from app.schema.schema import UserCreate
from app.services.authentication import AuthService

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

    if await auth_service.validate_for_registration(form_data):
        user = await auth_service.register_user(form_data)

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id), user.role)

        # set cookies
        response.set_cookie(
            "refreshToken",
            refresh_token,
            httponly=True,
            secure=settings.is_prod,
            samesite="none" if settings.is_prod else "lax",
            max_age=60
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
