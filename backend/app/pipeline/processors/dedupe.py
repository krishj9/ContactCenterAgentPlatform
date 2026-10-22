"""Hash-based deduplication processor."""

from collections.abc import Iterable

from app.pipeline.schemas.normalized_record import NormalizedRecord


def dedupe_records(records: Iterable[NormalizedRecord]) -> list[NormalizedRecord]:
    """Deduplicate records by content hash.

    Args:
        records: Iterable of normalized records.

    Returns:
        List of deduplicated records, preserving order of first occurrence.
    """
    seen: set[str] = set()
    output: list[NormalizedRecord] = []
    for record in records:
        if record.content_hash in seen:
            continue
        seen.add(record.content_hash)
        output.append(record)
    return output
