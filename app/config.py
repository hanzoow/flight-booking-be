from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    legacy_base_url: str = "https://mock-travel-api.vercel.app"
    http_timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_min_wait_seconds: float = 0.5
    retry_max_wait_seconds: float = 4.0

    circuit_failure_threshold: int = 5
    circuit_open_seconds: float = 30.0

    airport_cache_ttl_seconds: int = 3600
    booking_cache_ttl_seconds: int = 60


def get_settings() -> Settings:
    return Settings()
