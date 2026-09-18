"""Cấu hình ứng dụng đọc từ biến môi trường hoặc tệp .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "Growup API"
    app_env: str = "development"
    database_url: str | None = None
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "growup"
    db_user: str = "growup"
    db_password: str = ""
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    session_hours: int = 12
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
