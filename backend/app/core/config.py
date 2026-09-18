"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ROOT_DIR = _BACKEND_DIR.parent
_ENV_FILES = (
    str(_ROOT_DIR / ".env"),
    str(_BACKEND_DIR / ".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="postgresql+psycopg://darukaa:darukaa@localhost:5433/darukaa_ai"
    )

    llm_provider: str = Field(default="mock")
    llm_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o-mini")
    llm_base_url: str = Field(default="")

    embedding_provider: str = Field(default="mock")
    embedding_api_key: str = Field(default="")
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimensions: int = Field(default=384)

    cors_origins: str = Field(
        default=(
            "http://localhost:5174,http://127.0.0.1:5174,"
            "http://localhost:5173,http://localhost:3000"
        )
    )
    secret_key: str = Field(default="dev-secret-change-me")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    api_prefix: str = Field(default="/api/v1")

    retrieval_top_k: int = Field(default=6)
    retrieval_min_similarity: float = Field(default=0.15)

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("embedding_dimensions")
    @classmethod
    def validate_dims(cls, v: int) -> int:
        if v < 32 or v > 3072:
            raise ValueError("EMBEDDING_DIMENSIONS must be between 32 and 3072")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
