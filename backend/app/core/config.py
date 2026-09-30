"""Configuración validada y rutas independientes del directorio de ejecución."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "sqlite+aiosqlite:///./data/dashboard.db"
    frontend_url: HttpUrl = HttpUrl("http://localhost:3000")
    app_env: str = "development"

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=1, le=60 * 24 * 30)

    session_cookie_name: str = "dashboard_builder_session"
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_cookie_path: str = "/"
    session_cookie_domain: str | None = None

    @model_validator(mode="after")
    def validate_authentication_settings(self) -> "Settings":
        if len(self.jwt_secret_key.get_secret_value()) < 32:
            raise ValueError(
                "JWT_SECRET_KEY debe tener al menos 32 caracteres. "
                "Genera uno con: openssl rand -hex 32"
            )
        if self.app_env == "production" and self.jwt_algorithm == "none":
            raise ValueError("JWT_ALGORITHM no puede ser 'none' en producción.")
        if self.session_cookie_samesite == "none" and not self.session_cookie_secure:
            raise ValueError("SameSite=None exige cookies seguras (APP_ENV=production).")
        return self

    @property
    def database_connection_url(self) -> URL:
        url = make_url(self.database_url)
        if url.drivername == "sqlite+aiosqlite":
            if not url.database:
                raise ValueError("DATABASE_URL requiere una ruta SQLite persistente")
            if url.database != ":memory:":
                database_path = Path(url.database).expanduser()
                if not database_path.is_absolute():
                    database_path = BACKEND_DIR / database_path
                url = url.set(database=str(database_path.resolve()))
        return url

    @property
    def frontend_origin(self) -> str:
        return str(self.frontend_url).rstrip("/")

    @property
    def session_cookie_secure(self) -> bool:
        """Las cookies sólo viajan por HTTPS cuando el entorno es de producción."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
