"""Application settings and configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    APP_PROFILE: Literal["local", "gcp", "test"] = Field(
        default="test"
        if ("PYTEST_CURRENT_TEST" in os.environ or os.getenv("CC_APP_PROFILE") == "test")
        else "local",
        description="Deployment profile: local | gcp | test",
    )
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="cc-agent-platform-hmac-sha256-secret-key-32b",
        description="HMAC-SHA256 secret key for signing session join tokens.",
    )
    JWT_EXPIRATION_SECONDS: int = Field(
        default=900,
        description="TTL for WebSocket session join tokens (15 minutes).",
    )

    # Path configuration
    DATA_DIR: Path = Field(default_factory=lambda: Path("data"))

    # Vector store & corpus indexing limits (F3 fix: 0 means unlimited)
    MAX_RECORDS_PER_STORE: int = Field(
        default=0,
        description="Maximum records to index per store (0 for unlimited).",
    )
    # Embedding model configuration
    EMBEDDER_MODEL: str = Field(
        default="EmbeddingGemma",
        description="Active dense embedding model name.",
    )
    EMBEDDING_DIM: int = Field(
        default=768,
        description="Dense vector dimensionality.",
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=50,
        description="Batch size for embedding generation.",
    )

    # Operational thresholds and calibration values
    INTENT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.70,
        description="Minimum calibrated confidence to route to grounded RAG without warning.",
    )
    INTENT_OOS_THRESHOLD: float = Field(
        default=0.55,
        description="Out-of-scope confidence threshold tau_oos.",
    )
    INTENT_DEBOUNCE_MS: int = Field(
        default=300,
        description="Debounce interval in milliseconds for live customer speech turn classification.",
    )
    INTENT_SERVICE_URL: str = Field(
        default="http://localhost:8001/v1/classify",
        description="Endpoint URL for intent-svc ONNX Runtime microservice.",
    )
    GROUNDING_SIMILARITY_THRESHOLD: float = Field(
        default=0.75,
        description="Minimum cosine similarity required to consider policy chunk supportive.",
    )
    RERANK_TOP_K: int = 5
    RETRIEVAL_TOP_K: int = 10

    # Persistence endpoints (for local and GCP profiles)
    POSTGRES_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cc_platform"
    REDIS_URL: str = "redis://localhost:6379/0"
    GCS_BUCKET: str = "cc-agent-platform-raw"

    # GCP Cloud Run / Vertex AI settings
    GCP_PROJECT: str = Field(
        default="cc-agent-platform-dev",
        description="GCP Project ID for Vertex AI, Cloud Run, and Cloud SQL.",
    )
    GCP_REGION: str = Field(
        default="us-central1",
        description="GCP primary region.",
    )
    VERTEX_INTENT_ENDPOINT_URL: str = Field(
        default="http://localhost:8001/v1/classify",
        description="Vertex AI Endpoint URL or proxy for intent classification.",
    )
    GEMINI_MODEL: str = Field(
        default="gemini-3.8-flash",
        description="Active Gemini model name on Vertex AI.",
    )
    USE_GCP_LLM: bool = Field(
        default=True,
        description="Whether to use real GCP Vertex AI Gemini LLM in local profile.",
    )

    @property
    def corpus_paths(self) -> CorpusPaths:
        """Return configured CorpusPaths instance."""
        return CorpusPaths(root_dir=self.DATA_DIR)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
