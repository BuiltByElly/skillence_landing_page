from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import init_async_db
from app.main import app
from app.models.models import UserRole
from app.schema.schema import UserCreate


#  Create engine fixture that uses in-memory SQLite
@pytest_asyncio.fixture(name="test_engine", scope="session", loop_scope="session")
async def engine():
    """Create test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:?cache=shared",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()


# Create session fixture
@pytest_asyncio.fixture(scope="function")
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with session_factory() as session:
            yield session

    await transaction.rollback()


# Create client fixture
@pytest_asyncio.fixture(scope="function")
async def client(session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide async FastAPI test client"""
    app.dependency_overrides[init_async_db] = lambda: session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# Test data for testing
@pytest.fixture
def test_user_credentials() -> UserCreate:
    return UserCreate(
        username="elly", password="123456", email="e@g.com", role=UserRole.tutor
    )


@pytest_asyncio.fixture(scope="function")
async def test_user(session: AsyncSession):
    from uuid import uuid7

    from app.core.security import hash_password
    from app.models.models import Users

    user = Users(
        id=uuid7(),
        username="elly",
        password=hash_password("123456"),
        role=UserRole.tutor,
        email="e@g.com",
    )
    session.add(user)
    await session.commit()
    return user
