"""Domain models for retrieved evidence and policy/FAQ chunks."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceChunk:
    """A single retrieved evidence chunk with citation lineage."""

    chunk_id: str
    store_type: str  # "policy" | "faq"
    title: str
    text: str
    similarity_score: float
    intent_labels: list[str] = field(default_factory=list)
    corpus_version: str = "kb-v1"
    source_uri: str | None = None
    risk_level: str | None = None

    @property
    def is_policy(self) -> bool:
        return self.store_type == "policy"

    @property
    def is_faq(self) -> bool:
        return self.store_type == "faq"
