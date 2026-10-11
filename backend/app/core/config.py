"""Application settings loaded from environment variables / backend/.env."""

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "CodeArena API"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Stored as a comma-separated string so it is easy to set from the shell.
    CORS_ORIGINS: str = "http://localhost:5173"

    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10
    REGISTER_RATE_LIMIT_PER_MINUTE: int = 5

    # --- Code execution (Judge0). Student code only ever runs inside Judge0's
    # sandbox; these values stay server-side and never reach the frontend.
    JUDGE0_BASE_URL: str | None = None  # e.g. http://127.0.0.1:2358 (unset = execution unavailable)
    JUDGE0_API_KEY: str | None = None  # Judge0 AUTHN_TOKEN (or RapidAPI key)
    JUDGE0_API_KEY_HEADER: str = "X-Auth-Token"  # "X-RapidAPI-Key" for the hosted RapidAPI service
    JUDGE0_RAPIDAPI_HOST: str | None = None  # only for the hosted RapidAPI service
    JUDGE0_REQUEST_TIMEOUT: float = 10.0  # seconds per HTTP call to Judge0
    JUDGE0_TIMEOUT: float = 30.0  # seconds a whole run/submission may wait for Judge0
    JUDGE0_POLL_INTERVAL: float = 0.75  # seconds between result polls
    JUDGE0_MAX_CONCURRENT_JOBS: int = 4  # executions in flight from this backend process
    EXECUTION_MAX_SOURCE_BYTES: int = 200_000
    EXECUTION_MAX_OUTPUT_BYTES: int = 64_000  # stdout/stderr kept per test (Judge0 also caps output)
    EXECUTION_STOP_ON_FIRST_FAILURE: bool = True
    RUN_RATE_LIMIT_PER_MINUTE: int = 10
    SUBMIT_RATE_LIMIT_PER_MINUTE: int = 5

    # --- Progress & analytics. Calendar days (streaks, heatmap, "today") are
    # counted in ONE application timezone for everybody, never the browser's
    # or the server's local time. Use your institution's IANA timezone name.
    APP_TIMEZONE: str = "Asia/Kolkata"

    # bcrypt work factor for new password hashes (existing hashes keep theirs).
    BCRYPT_ROUNDS: int = 12

    ADMIN_NAME: str = "CodeArena Admin"
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    STAFF_NAME: str = "Staff Member"
    STAFF_EMAIL: str | None = None
    STAFF_PASSWORD: str | None = None

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_must_be_strong(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return value

    @field_validator("APP_TIMEZONE")
    @classmethod
    def timezone_must_exist(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"APP_TIMEZONE must be an IANA timezone name such as 'Asia/Kolkata' or 'UTC' (got {value!r})") from exc
        return value

    @field_validator("BCRYPT_ROUNDS")
    @classmethod
    def bcrypt_rounds_in_range(cls, value: int) -> int:
        if not 4 <= value <= 16:
            raise ValueError("BCRYPT_ROUNDS must be between 4 and 16")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
