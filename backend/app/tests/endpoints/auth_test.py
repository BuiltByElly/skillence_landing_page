
import httpx

from app.models.models import Users


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

    async def test_registration_validation_error(
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
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "elly",
                "password": "123456",
                "role": "tutor",
                "email": "e@g.com",
            },
        )
        assert response.status_code == 400
