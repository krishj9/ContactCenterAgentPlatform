"""Unit Tests for Cloud Sensitive Data Protection (DLP) Redactor (Phase P10.3).

Verifies that PANs, SSNs, phone numbers, and emails are redacted while preserving
masked last-4 digits for customer reference.
"""

from __future__ import annotations

import pytest

from app.adapters.gcp.dlp_redactor import GoogleCloudDLPRedactor


@pytest.fixture
def redactor() -> GoogleCloudDLPRedactor:
    return GoogleCloudDLPRedactor(preserve_last_four_digits=True)


@pytest.mark.asyncio
async def test_redacts_credit_card_and_preserves_last_four(
    redactor: GoogleCloudDLPRedactor,
) -> None:
    """Verify 16-digit credit card PAN is redacted with masked last-4 retained."""
    transcript = "Customer says: My card number is 4532 1122 3344 3312 and it was declined."
    redacted = await redactor.redact(transcript)

    assert "4532 1122 3344 3312" not in redacted
    assert "[REDACTED_CARD_****3312]" in redacted
    assert "was declined" in redacted


@pytest.mark.asyncio
async def test_redacts_ssn_formatted_and_unformatted(redactor: GoogleCloudDLPRedactor) -> None:
    """Verify SSNs are redacted."""
    transcript = "SSN is 987-65-4321 for verification."
    redacted = await redactor.redact(transcript)

    assert "987-65-4321" not in redacted
    assert "[REDACTED_SSN]" in redacted


@pytest.mark.asyncio
async def test_redacts_email_and_phone(redactor: GoogleCloudDLPRedactor) -> None:
    """Verify email and phone numbers are redacted."""
    transcript = "Contact me at user.support@example.com or call 415-555-2671."
    redacted = await redactor.redact(transcript)

    assert "user.support@example.com" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "415-555-2671" not in redacted
    assert "[REDACTED_PHONE]" in redacted


@pytest.mark.asyncio
async def test_leaves_benign_text_unaltered(redactor: GoogleCloudDLPRedactor) -> None:
    """Verify standard dollar amounts, transaction dates, and non-PII text are unchanged."""
    transcript = "I deposited $50.00 on March 15th at branch 104."
    redacted = await redactor.redact(transcript)

    assert redacted == transcript
