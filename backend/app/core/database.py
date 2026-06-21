from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

# Creating async engine
async_engine = create_async_engine(settings.DATABASE_URL)


# create async session maker
async_session_factory = async_sessionmaker(bind=async_engine, class_=AsyncSession)
