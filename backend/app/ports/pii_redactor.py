"""Port protocol for PII redaction and sensitive data protection."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PIIRedactor(Protocol):
    """Protocol for sensitive PII redaction (PAN, SSN, tokens)."""

    async def redact(self, text: str) -> str:
        """Redact sensitive PII tokens from text."""
        ...
