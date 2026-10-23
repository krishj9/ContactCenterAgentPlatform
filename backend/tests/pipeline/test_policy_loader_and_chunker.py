"""Unit tests for policy loader, normalizer, and heading-aware chunker (P3.4)."""

from __future__ import annotations

from pathlib import Path

from app.pipeline.loaders.policy_loader import (
    load_policy_markdown_files,
    validate_policy_frontmatter,
)
from app.pipeline.normalizers.policy_normalizer import PolicyNormalizer
from app.pipeline.processors.chunking import (
    HeadingAwareMarkdownChunker,
    estimate_tokens,
)


def test_validate_frontmatter_rules() -> None:
    valid_fm = {
        "policy_id": "POL-CARD-DECLINE-01",
        "version": "v1.0",
        "title": "Valid Card Policy",
        "intent_labels": ["card_declined"],
        "risk_level": "medium",
        "owner": "Card Ops",
        "effective_from": "2026-01-01",
        "status": "active",
    }
    errors = validate_policy_frontmatter(valid_fm, Path("test.md"))
    assert errors == []

    invalid_fm = {
        "policy_id": "invalid_id",
        "version": "invalid",
        "title": "Short",
        "intent_labels": [],
        "risk_level": "extreme",
        "owner": "",
        "effective_from": "bad_date",
        "status": "unknown",
    }
    errors = validate_policy_frontmatter(invalid_fm, Path("bad.md"))
    assert len(errors) >= 5


def test_load_and_normalize_authored_policies() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    policy_dir = repo_root / "corpora" / "policy"

    policies = list(load_policy_markdown_files(policy_dir))
    assert len(policies) == 8

    normalizer = PolicyNormalizer()
    for raw in policies:
        norm = normalizer.normalize(raw)
        assert norm is not None
        assert norm.title == raw["title"]
        assert norm.store_type == "policy"
        assert norm.source == "policy"
        assert norm.content_hash is not None
        assert len(norm.metadata.extra["intent_labels"]) >= 1


def test_heading_aware_chunker_preserves_procedures_and_headers() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    policy_dir = repo_root / "corpora" / "policy"

    policies = list(load_policy_markdown_files(policy_dir))
    normalizer = PolicyNormalizer()
    chunker = HeadingAwareMarkdownChunker(target_min_tokens=200, target_max_tokens=500)

    for raw in policies:
        norm = normalizer.normalize(raw)
        assert norm is not None
        chunks = chunker.chunk_record(norm)
        assert len(chunks) >= 4  # Each policy has at least 5 main sections

        for c in chunks:
            assert c.policy_id == raw["policy_id"]
            # Preserves heading in title or prefix
            assert raw["title"] in c.text or raw["title"] in c.title
            assert "Section:" in c.text
            # Token counts within reasonable bounds
            assert 10 <= c.token_count <= 600


def test_token_estimator() -> None:
    text = "This is a simple sentence for token estimation testing."
    tokens = estimate_tokens(text)
    assert 9 <= tokens <= 15
