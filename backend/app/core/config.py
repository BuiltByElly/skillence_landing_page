from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str
    DUMMY_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    REFRESH_TOKEN_EXPIRE_DAY: int
    ENV: Literal["production", "development"]

    model_config = {"env_file": ".env"}

    @property
    def is_prod(self):
        """
        Check if the environment is in production
        """
        return self.ENV == "production"


settings = Settings()  # type: ignore
