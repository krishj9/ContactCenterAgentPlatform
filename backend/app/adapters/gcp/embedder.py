"""GCP Vertex AI dense embedding adapter using gemini-embedding-001 / text-embedding-004."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class VertexAIEmbedder:
    """Embedder port adapter connecting to GCP Vertex AI text embeddings endpoint."""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        model_name: str = "text-embedding-004",
        dimension: int = 768,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.dimension = dimension
        self._client: Any | None = None

    @property
    def dim(self) -> int:
        """Vector dimensionality."""
        return self.dimension

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import vertexai
                from vertexai.language_models import TextEmbeddingModel

                settings = get_settings()
                proj = self.project_id or getattr(settings, "GCP_PROJECT", "cc-agent-platform-dev")
                vertexai.init(project=proj, location=self.location)
                self._client = TextEmbeddingModel.from_pretrained(self.model_name)
            except Exception as e:
                logger.info(
                    "Vertex AI SDK not available offline (%s). Using deterministic dense embedding fallback.",
                    e,
                )
        return self._client

    async def embed_texts(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """Compute dense vector embeddings for input documents."""
        client = self._get_client()
        if client is not None:
            try:
                from vertexai.language_models import TextEmbeddingInput

                inputs = [TextEmbeddingInput(t, "RETRIEVAL_DOCUMENT") for t in texts]
                embeddings = client.get_embeddings(inputs, output_dimensionality=self.dimension)
                return [e.values for e in embeddings]
            except Exception as e:
                logger.warning("Vertex AI embed_texts call failed (%s). Falling back.", e)

        # Deterministic offline fallback embedding
        return [self._mock_embed(t) for t in texts]

    async def embed_query(self, query: str) -> list[float]:
        """Compute dense vector embedding for search query."""
        client = self._get_client()
        if client is not None:
            try:
                from vertexai.language_models import TextEmbeddingInput

                inputs = [TextEmbeddingInput(query, "RETRIEVAL_QUERY")]
                embeddings = client.get_embeddings(inputs, output_dimensionality=self.dimension)
                return embeddings[0].values
            except Exception as e:
                logger.warning("Vertex AI embed_query call failed (%s). Falling back.", e)

        return self._mock_embed(query)

    def _mock_embed(self, text: str) -> list[float]:
        import hashlib

        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [(b / 255.0) * 2.0 - 1.0 for b in h]
        while len(vec) < self.dimension:
            vec.extend(vec[: min(len(vec), self.dimension - len(vec))])
        vec = vec[: self.dimension]
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]
