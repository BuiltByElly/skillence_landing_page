from typing import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import async_session_factory


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            pass
