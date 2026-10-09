"""Runtime configuration for the accounts service."""
import os
from functools import lru_cache
from pathlib import Path

DEFAULT_SECRET_FILE = "/run/secrets/app/secret_key"


def _load_secret_key() -> str:
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = Path(os.environ.get("SECRET_KEY_FILE", DEFAULT_SECRET_FILE))
    if path.exists():
        return path.read_text().strip()
    raise RuntimeError(f"SECRET_KEY is not set and {path} does not exist")


class Settings:
    def __init__(self) -> None:
        self.service_name = "acme-accounts"
        self.version = "1.4.2"
        self.environment = os.environ.get("APP_ENV", "dev")
        self.secret_key = _load_secret_key()
        self.token_ttl_seconds = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))
        self.telemetry_url = os.environ.get("TELEMETRY_URL", "http://localhost:9009/collect")

    def as_dict(self, redact: bool = True) -> dict:
        return {
            "service_name": self.service_name,
            "version": self.version,
            "environment": self.environment,
            "secret_key": "********" if redact else self.secret_key,
            "token_ttl_seconds": self.token_ttl_seconds,
            "telemetry_url": self.telemetry_url,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
