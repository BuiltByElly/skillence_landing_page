import httpx

from app.models.models import Users
from app.schema.schema import UserCreate, UserLogin


class TestRegistrationEndpoint:
    async def test_registration_success(
        self,
        client: httpx.AsyncClient,
    ):

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "ellyyy",
                "password": "123456",
                "role": "tutor",
                "email": "g@e.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["message"] == "Registered successfully"
        assert "accessToken" in response.json()
        assert response.cookies.get("refreshToken") is not None

    async def test_registration_validation_for_registration_error(
        self,
        client: httpx.AsyncClient,
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "",
                "password": "",
                "role": "tutor",
                "email": "w@g.com",
            },
        )
        assert response.status_code == 401

    async def test_registration_unique_constraint_error(
        self,
        client: httpx.AsyncClient,
        test_user: Users,
        test_user_credentials: UserCreate,
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "elly",
                "password": "123456",
                "role": "tutor",
                "email": test_user_credentials.email,
            },
        )
        assert response.status_code == 400


class TestAuthenticationEndpoint:
    async def test_authentication_success(
        self, test_user, test_user_credentials: UserLogin, client: httpx.AsyncClient
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "123456", "email": test_user_credentials.email},
        )

        assert response.status_code == 200

    async def test_authentication_error(
        self, test_user, test_user_credentials: UserLogin, client: httpx.AsyncClient
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "12346", "email": test_user_credentials.email},
        )

        assert response.status_code == 401
