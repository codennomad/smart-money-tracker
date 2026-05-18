from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Smart Money Tracker"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str  # required — no default
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # Database
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host/db

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # SEC EDGAR — only these domains are allowed for outbound HTTP
    ALLOWED_EXTERNAL_DOMAINS: list[str] = [
        "data.sec.gov",
        "www.sec.gov",
        "efts.sec.gov",
        "www.finra.org",
        "api.finra.org",
        "disclosures.house.gov",
        "efts.senate.gov",
    ]

    # Rate limits
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_HEAVY: str = "10/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
