"""Test adapter for PIIRedactor port."""

from __future__ import annotations

import re


class TestPIIRedactor:
    """Deterministic regex redactor for testing offline without external services."""

    __test__ = False

    def __init__(self) -> None:
        # Matches 16-digit PANs with optional spaces or hyphens
        self._pan_pattern = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
        # Matches SSN format XXX-XX-XXXX
        self._ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    async def redact(self, text: str) -> str:
        text = self._pan_pattern.sub("[REDACTED_PAN]", text)
        text = self._ssn_pattern.sub("[REDACTED_SSN]", text)
        return text
