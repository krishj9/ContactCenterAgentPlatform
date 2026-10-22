"""Text normalization utilities."""

import re


def clean_text(value: str | None) -> str:
    """Normalize text: NBSP cleanup, whitespace normalization, trim."""
    if not value:
        return ""
    # Replace non-breaking spaces with regular spaces
    value = value.replace("\u00a0", " ")
    # Collapse multiple whitespace to single space
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clip_text(value: str, max_chars: int) -> str:
    """Clip text to max_chars, add ellipsis if truncated."""
    value = value.strip()
    return value if len(value) <= max_chars else value[: max_chars - 3] + "..."
