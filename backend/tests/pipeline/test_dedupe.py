"""Tests for deduplication processor."""

from app.pipeline.processors.dedupe import dedupe_records
from app.pipeline.schemas.normalized_record import (
    NormalizedMetadata,
    NormalizedRecord,
    SourceType,
    StoreType,
)


def create_record(id_suffix: str, content_hash: str) -> NormalizedRecord:
    """Helper to create a test record."""
    return NormalizedRecord(
        id=f"test-{id_suffix}",
        source=SourceType.BANKING77,
        store_type=StoreType.INTENT,
        text="Test text",
        text_for_embedding="Test embedding",
        metadata=NormalizedMetadata(
            dataset=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            use_case="test",
        ),
        content_hash=content_hash,
    )


def test_identical_hashes_collapse_to_one():
    """Test that records with identical content hashes collapse to one."""
    records = [
        create_record("1", "sha256:abc123"),
        create_record("2", "sha256:abc123"),
        create_record("3", "sha256:abc123"),
    ]
    deduped = dedupe_records(records)
    assert len(deduped) == 1
    assert deduped[0].id == "test-1"


def test_distinct_records_remain():
    """Test that records with distinct hashes remain."""
    records = [
        create_record("1", "sha256:abc123"),
        create_record("2", "sha256:def456"),
        create_record("3", "sha256:ghi789"),
    ]
    deduped = dedupe_records(records)
    assert len(deduped) == 3


def test_preserves_order_of_first_occurrence():
    """Test that deduplication preserves order of first occurrence."""
    records = [
        create_record("1", "sha256:abc123"),
        create_record("2", "sha256:def456"),
        create_record("3", "sha256:abc123"),
        create_record("4", "sha256:ghi789"),
        create_record("5", "sha256:def456"),
    ]
    deduped = dedupe_records(records)
    assert len(deduped) == 3
    assert deduped[0].id == "test-1"
    assert deduped[1].id == "test-2"
    assert deduped[2].id == "test-4"


def test_empty_list_returns_empty():
    """Test that empty list returns empty."""
    deduped = dedupe_records([])
    assert len(deduped) == 0
