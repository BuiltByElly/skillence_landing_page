from sqlmodel.ext.asyncio.session import AsyncSession

from app.schema.schema import UserCreate
from app.services.authentication import AuthService


class TestValidation:
    async def test_validate_for_register_with_success(
        self, session: AsyncSession, test_user_credentials: UserCreate
    ):
        auth_service = AuthService(session)
        result = await auth_service.validate_for_registration(test_user_credentials)
        assert result is True

    # def test_validate_for_register_with_unavailable_email_and_fullname(
    #     self, session, test_user_credentials, test_user
    # ):

    #     with pytest.raises(HTTPException) as exec:
    #         auth_service = AuthService(session)
    #         auth_service.validate_for_registration(test_user_credentials)
    #     assert not exec.value

    # def test_validate_for_login_with_success(self, session, test_user_credentials):
    #     auth_service = AuthService(session)

    #     result = auth_service.validate_for_login(
    #         test_user_credentials["password"],
    #         test_user_credentials["email"],
    #     )
    #     assert result is True

    # def test_validate_for_login_with_failure(self, session, test_user_credentials):
    #     auth_service = AuthService(session)

    #     with pytest.raises(HTTPException) as exec:
    #         auth_service.validate_for_login(
    #             "",
    #             "2.com",
    #         )
    #     assert exec.value.status_code == 401
