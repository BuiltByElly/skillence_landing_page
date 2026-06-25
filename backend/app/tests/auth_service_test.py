import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schema.schema import UserLogin
from app.services.authentication import AuthService


class Test_for_registration:
    async def test_registration_with_success(
        self, session: AsyncSession, test_user_credentials
    ):
        auth_service = AuthService(session)

        user = await auth_service.register_user(test_user_credentials)

        assert user is not None

    async def test_registration_integrity_error(
        self, session: AsyncSession, test_user_credentials
    ):
        auth_service = AuthService(session)
        await auth_service.register_user(test_user_credentials)

        with pytest.raises(HTTPException) as exec:
            await auth_service.register_user(test_user_credentials)

        assert exec.value.status_code == 400


class Test_for_authentication:
    async def test_authentication_with_success(
        self, session: AsyncSession, test_user_credentials, test_user
    ):
        auth_service = AuthService(session)

        user = await auth_service.authenticate_user(test_user_credentials)

        assert user is not None

    async def test_authentication_with_error(
        self, session: AsyncSession, test_user_credentials, test_user
    ):
        auth_service = AuthService(session)

        with pytest.raises(HTTPException) as exec:
            await auth_service.authenticate_user(
                UserLogin(email="t@g.com", password="12345")
            )

        assert exec.value.status_code == 401
