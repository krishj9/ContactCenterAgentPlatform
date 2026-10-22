"""Deterministic ID generation utilities."""

import re


def slugify(value: str) -> str:
    """Convert text to lowercase slug (alphanumeric + hyphens)."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_id(*parts: str) -> str:
    """Build deterministic ID from parts, joined by hyphens."""
    return "-".join(slugify(part) for part in parts if part)
