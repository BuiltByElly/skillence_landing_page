from typing import AsyncGenerator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.dependencies import get_async_db
from app.main import app
from app.models.models import UserRole
from app.schema.schema import UserCreate


#  Create engine fixture that uses in-memory SQLite
@pytest.fixture(name="test_engine", scope="session")
async def engine():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine


# Create session fixture
@pytest.fixture()
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession)

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with session_factory() as session:
        try:
            yield session
        finally:
            pass

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# Create client fixture
@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide async FastAPI test client"""
    app.dependency_overrides[get_async_db] = lambda: session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# Test data for testing
@pytest.fixture
def test_user_credentials() -> UserCreate:
    return UserCreate(
        fullname="elly eroms", password="1234", email="e@g.com", role=UserRole.tutor
    )


@pytest.fixture
async def test_user(session: AsyncSession):
    from uuid import uuid7

    from app.core.security import hash_password
    from app.models.models import Users

    user = Users(
        id=uuid7(),
        fullname="elly",
        password=hash_password("123456"),
        role=UserRole.tutor,
        email="e@g.com",
    )
    session.add(user)
    await session.commit()
    return user
