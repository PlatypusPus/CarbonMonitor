"""Application settings loaded from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"

    cors_origins: str = "http://localhost,http://localhost:5173"

    database_url: str = "postgresql+psycopg://carbontrace:carbontrace@localhost:5432/carbontrace"

    elasticsearch_url: str = "http://localhost:9200"
    logstash_url: str = "http://localhost:8080"

    jwt_secret_key: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    electricity_maps_api_key: str = ""
    carbon_interface_api_key: str = ""
    openweathermap_api_key: str = ""
    poll_interval_minutes: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def assert_production_ready(self) -> None:
        if self.is_production and self.jwt_secret_key == "dev-insecure-change-me":
            raise RuntimeError(
                "JWT_SECRET_KEY is still the insecure default; set a strong secret "
                "before running with ENVIRONMENT=production."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
