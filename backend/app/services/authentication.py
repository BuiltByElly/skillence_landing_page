from datetime import datetime, timedelta, timezone

from anyio import to_thread
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

from app.core.config import settings
from app.core.security import (
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.models import RefreshTokens, Users
from app.schema.schema import UserCreate, UserJWT, UserLogin

security = HTTPBearer()


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def validation_for_registration(self, form_data: UserCreate) -> bool:
        if form_data.password.strip() == "" or form_data.username.strip() == "":
            await to_thread.run_sync(hash_password, settings.DUMMY_PASSWORD)
            return False
        return True

    async def validation_for_authentication(self, form_data: UserLogin) -> bool:
        if form_data.password.strip() == "":
            await to_thread.run_sync(hash_password, settings.DUMMY_PASSWORD)
            return False
        return True

    async def register_user(self, form_data: UserCreate):
        hashed_password = await to_thread.run_sync(hash_password, form_data.password)
        try:
            new_user = Users(
                username=form_data.username,
                password=hashed_password,
                email=form_data.email,
                role=form_data.role,
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user

        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="User already exist",
            )

    async def write_refresh_token_to_db(
        self, refresh_token: str, user: Users, remember_me: bool = False
    ):

        if not user.id:
            return

        refresh_token_hash = hash_refresh_token(refresh_token)
        new_refresh_token_hash = RefreshTokens(
            token_hash=refresh_token_hash,
            user_id=user.id,
            role=user.role,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc)
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                if remember_me
                else settings.REFRESH_TOKEN_EXPIRE_DAY
            ),
        )
        self.db.add(new_refresh_token_hash)
        await self.db.commit()

    async def authenticate_user(self, form_data: UserLogin):
        users = await self.db.exec(select(Users).where(Users.email == form_data.email))
        user = users.first()
        if user:
            if await to_thread.run_sync(
                verify_password, form_data.password, user.password
            ):
                return user

        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Authorization failed"
        )

    async def validate_refresh_token(self, refresh_token: str):
        token_hash = hash_refresh_token(refresh_token)

        now = datetime.now(timezone.utc)

        # validate refresh token exists in database
        db_refresh_tokens = await self.db.exec(
            select(RefreshTokens).where(RefreshTokens.token_hash == token_hash)
        )
        db_refresh_token = db_refresh_tokens.first()

        if not db_refresh_token:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized"
            )
        if db_refresh_token.revoked:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Refresh Token"
            )
        if db_refresh_token.expires_at.replace(tzinfo=timezone.utc) < now:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Token Expired"
            )

        # Revoke old refresh token
        db_refresh_token.revoked = True
        self.db.add(db_refresh_token)
        await self.db.commit()
        return True

    async def logout_user(self, refresh_token: str):
        token_hash = hash_refresh_token(refresh_token)

        # validate refresh token
        db_refresh_tokens = await self.db.exec(
            select(RefreshTokens).where(RefreshTokens.token_hash == token_hash)
        )
        db_refresh_token = db_refresh_tokens.first()

        if not db_refresh_token:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="An error occurred while logging",
            )
        db_refresh_token.revoked = True

        self.db.add(db_refresh_token)
        await self.db.commit()


def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Extract and validate the current user from access token."""
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="No access token found"
        )
    payload = decode_token(token, token_type="access")
    user_jwt: UserJWT = UserJWT(sub=payload["sub"], role=payload["role"])

    request.state.__setattr__("public_id", user_jwt.sub)

    return user_jwt
