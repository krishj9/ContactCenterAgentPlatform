"""Tests for normalized record schema."""

from datetime import UTC, datetime

import pytest

from app.pipeline.schemas.normalized_record import (
    NormalizedMetadata,
    NormalizedRecord,
    SourceType,
    StoreType,
)


def test_valid_normalized_record():
    """Test that a valid NormalizedRecord can be created."""
    record = NormalizedRecord(
        id="test-1",
        source=SourceType.BANKING77,
        store_type=StoreType.INTENT,
        title="Test Intent",
        text="This is a test utterance",
        text_for_embedding="Intent example: This is a test utterance",
        metadata=NormalizedMetadata(
            dataset=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            intent_label="test_intent",
            use_case="intent_example",
        ),
        content_hash="sha256:abc123",
    )
    assert record.id == "test-1"
    assert record.source == SourceType.BANKING77
    assert record.store_type == StoreType.INTENT


def test_empty_text_rejected():
    """Test that empty text is rejected."""
    with pytest.raises(ValueError, match="text fields must not be empty"):
        NormalizedRecord(
            id="test-1",
            source=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            text="",
            text_for_embedding="Intent example: test",
            metadata=NormalizedMetadata(
                dataset=SourceType.BANKING77,
                store_type=StoreType.INTENT,
                use_case="intent_example",
            ),
            content_hash="sha256:abc123",
        )


def test_empty_text_for_embedding_rejected():
    """Test that empty text_for_embedding is rejected."""
    with pytest.raises(ValueError, match="text fields must not be empty"):
        NormalizedRecord(
            id="test-1",
            source=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            text="This is a test utterance",
            text_for_embedding="",
            metadata=NormalizedMetadata(
                dataset=SourceType.BANKING77,
                store_type=StoreType.INTENT,
                use_case="intent_example",
            ),
            content_hash="sha256:abc123",
        )


def test_whitespace_only_text_rejected():
    """Test that whitespace-only text is rejected."""
    with pytest.raises(ValueError, match="text fields must not be empty"):
        NormalizedRecord(
            id="test-1",
            source=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            text="   \n\t  ",
            text_for_embedding="Intent example: test",
            metadata=NormalizedMetadata(
                dataset=SourceType.BANKING77,
                store_type=StoreType.INTENT,
                use_case="intent_example",
            ),
            content_hash="sha256:abc123",
        )


def test_created_at_defaults_to_now():
    """Test that created_at defaults to current time."""
    before = datetime.now(UTC)
    record = NormalizedRecord(
        id="test-1",
        source=SourceType.BANKING77,
        store_type=StoreType.INTENT,
        text="Test text",
        text_for_embedding="Test embedding",
        metadata=NormalizedMetadata(
            dataset=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            use_case="test",
        ),
        content_hash="sha256:abc123",
    )
    after = datetime.now(UTC)
    assert before <= record.created_at <= after
