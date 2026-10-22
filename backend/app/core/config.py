"""Application settings and configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.pipeline.paths import CorpusPaths


class Settings(BaseSettings):
    """Central configuration for backend services and data pipelines."""

    model_config = SettingsConfigDict(
        env_prefix="CC_",
        env_file=".env",
        extra="ignore",
    )

    APP_NAME: str = "Contact Center Agent Helper Platform"
    APP_PROFILE: str = Field(default="local", description="Deployment profile: local | gcp | test")
    DEBUG: bool = False

    # Path configuration
    DATA_DIR: Path = Field(default_factory=lambda: Path("data"))

    # Vector store & corpus indexing limits (F3 fix: 0 means unlimited)
    MAX_RECORDS_PER_STORE: int = Field(
        default=0,
        description="Maximum records to index per store (0 for unlimited).",
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=50,
        description="Batch size for embedding generation.",
    )

    @property
    def corpus_paths(self) -> CorpusPaths:
        """Return configured CorpusPaths instance."""
        return CorpusPaths(root_dir=self.DATA_DIR)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
