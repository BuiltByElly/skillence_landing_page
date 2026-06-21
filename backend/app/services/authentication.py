from datetime import datetime, timedelta, timezone

from anyio import to_thread
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, hash_refresh_token
from app.models.models import RefreshTokens, Users
from app.schema.schema import UserCreate


class AuthService:
    async def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def validate_for_registration(self, form_data: UserCreate) -> bool:
        exists_in_db = await self.db.exec(
            select(Users.email, Users.fullname).where(
                (form_data.email == Users.email)
                or (form_data.fullname == Users.fullname)
            )
        )

        if not form_data.password.strip() == "":
            if not exists_in_db.first():
                return True
        return False

    async def register_user(self, form_data: UserCreate):
        hashed_password = await to_thread.run_sync(hash_password, form_data.password)
        new_user = Users(
            fullname=form_data.fullname,
            password=hashed_password,
            email=form_data.email,
            role=form_data.role,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

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
