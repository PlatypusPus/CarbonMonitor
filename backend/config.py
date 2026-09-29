"""Application settings loaded from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"

    cors_origins: str = "http://localhost,http://localhost:5173"

    database_url: str = "postgresql+psycopg://carbontrace:carbontrace@localhost:5432/carbontrace"

    jwt_secret_key: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    public_app_url: str = "http://localhost:5173"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "CarbonTrace <noreply@carbontrace.local>"
    smtp_starttls: bool = False
    smtp_ssl: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def assert_production_ready(self) -> None:
        if self.is_production and (not self.public_app_url.startswith("https://") or not (self.smtp_starttls or self.smtp_ssl)):
            raise RuntimeError("Production requires an HTTPS application URL and TLS email delivery")
        if self.is_production and self.jwt_secret_key == "dev-insecure-change-me":
            raise RuntimeError(
                "JWT_SECRET_KEY is still the insecure default; set a strong secret "
                "before running with ENVIRONMENT=production."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
