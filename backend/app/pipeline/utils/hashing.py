"""Hashing utilities for content deduplication."""

import hashlib


def sha256_text(value: str) -> str:
    """Return SHA256 hash of text, prefixed with 'sha256:'."""
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
