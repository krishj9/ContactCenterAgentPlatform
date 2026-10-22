"""Quality filtering processor."""

from app.pipeline.schemas.normalized_record import NormalizedRecord


def is_high_enough_quality(record: NormalizedRecord) -> bool:
    """Check if a record meets quality thresholds.

    Args:
        record: Normalized record to check.

    Returns:
        True if record passes quality checks, False otherwise.
    """
    if len(record.text_for_embedding) < 20:
        return False
    return True
