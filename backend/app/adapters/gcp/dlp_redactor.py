"""Google Cloud Sensitive Data Protection (DLP) Redactor Adapter (Spec §6.2, Phase P10.3).

Inspects and redacts sensitive PII (credit cards/PAN, SSN, emails, phone numbers, tax IDs)
from speech transcripts prior to database persistence or LLM prompt inclusion.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("app.adapters.gcp.dlp_redactor")

# Precompiled regex patterns for deterministic local redaction and test isolation
PAN_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SSN_REGEX = re.compile(r"\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b")
ITIN_REGEX = re.compile(r"\b9\d{2}[- ]?(?:5[0-9]|6[0-5]|7[0-9]|8[0-8]|9[0-2]|9[4-9])[- ]?\d{4}\b")


def passes_luhn_checksum(candidate: str) -> bool:
    """Validate digits string using ISO/IEC 7812 Luhn checksum."""
    digits = [int(c) for c in candidate if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            doubled = digit * 2
            checksum += doubled if doubled <= 9 else (doubled - 9)
        else:
            checksum += digit
    return (checksum % 10) == 0


class GoogleCloudDLPRedactor:
    """Cloud DLP Redactor adapter implementing the PIIRedactor port.

    Uses Google Cloud Sensitive Data Protection API in cloud production,
    with local rule-based regex and Luhn checksum fallback in test profile.
    """

    def __init__(
        self,
        project_id: str | None = None,
        preserve_last_four_digits: bool = True,
    ) -> None:
        self.settings = get_settings()
        self.project_id = (
            project_id
            or getattr(self.settings, "GCP_PROJECT_ID", None)
            or getattr(self.settings, "GCP_PROJECT", "test-project")
        )
        self.preserve_last_four = preserve_last_four_digits
        self._dlp_client: Any = None

    def _get_dlp_client(self) -> Any:
        if self._dlp_client is None:
            try:
                from google.cloud import dlp_v2

                self._dlp_client = dlp_v2.DlpServiceClient()
            except Exception as exc:
                logger.warning(f"Could not initialize Cloud DLP client: {exc}. Using local engine.")
                self._dlp_client = False
        return self._dlp_client

    async def redact(self, text: str) -> str:
        """Inspect and redact all sensitive PII tokens from text."""
        if not text:
            return ""

        # In test or local mock profiles, use local redaction engine
        if self.settings.APP_PROFILE in ("test", "local"):
            return self._redact_local(text)

        client = self._get_dlp_client()
        if not client or client is False:
            return self._redact_local(text)

        try:
            from google.cloud import dlp_v2

            parent = f"projects/{self.project_id}/locations/global"
            item = {"value": text}

            info_types = [
                {"name": "CREDIT_CARD_NUMBER"},
                {"name": "US_SOCIAL_SECURITY_NUMBER"},
                {"name": "EMAIL_ADDRESS"},
                {"name": "PHONE_NUMBER"},
                {"name": "US_INDIVIDUAL_TAX_IDENTIFIER"},
                {"name": "IBAN_CODE"},
            ]

            inspect_config = {
                "info_types": info_types,
                "min_likelihood": dlp_v2.Likelihood.LIKELY,
                "include_quote": True,
            }

            deidentify_config = {
                "info_type_transformations": {
                    "transformations": [
                        {
                            "info_types": [{"name": "CREDIT_CARD_NUMBER"}],
                            "primitive_transformation": {"replace_with_info_type_config": {}},
                        },
                        {
                            "info_types": [{"name": "US_SOCIAL_SECURITY_NUMBER"}],
                            "primitive_transformation": {"replace_with_info_type_config": {}},
                        },
                        {
                            "info_types": [{"name": "EMAIL_ADDRESS"}],
                            "primitive_transformation": {"replace_with_info_type_config": {}},
                        },
                        {
                            "info_types": [{"name": "PHONE_NUMBER"}],
                            "primitive_transformation": {"replace_with_info_type_config": {}},
                        },
                    ]
                }
            }

            response = client.deidentify_content(
                request={
                    "parent": parent,
                    "deidentify_config": deidentify_config,
                    "inspect_config": inspect_config,
                    "item": item,
                }
            )
            return response.item.value
        except Exception as exc:
            logger.warning(
                f"Cloud DLP deidentify call failed: {exc}. Falling back to local redaction."
            )
            return self._redact_local(text)

    def _redact_local(self, text: str) -> str:
        """High-performance local regex redaction for test and fallback modes."""
        redacted = text

        # 1. PAN / Credit Card Numbers
        def replace_pan(match: re.Match[str]) -> str:
            raw = match.group(0)
            digits = re.sub(r"\D", "", raw)
            if len(digits) >= 13 and (passes_luhn_checksum(digits) or len(digits) == 16):
                if self.preserve_last_four and len(digits) >= 4:
                    return f"[REDACTED_CARD_****{digits[-4:]}]"
                return "[REDACTED_CARD]"
            return raw

        redacted = PAN_REGEX.sub(replace_pan, redacted)

        # 2. SSN Numbers
        redacted = SSN_REGEX.sub("[REDACTED_SSN]", redacted)

        # 3. ITIN Numbers
        redacted = ITIN_REGEX.sub("[REDACTED_TAX_ID]", redacted)

        # 4. Email Addresses
        redacted = EMAIL_REGEX.sub("[REDACTED_EMAIL]", redacted)

        # 5. Phone Numbers
        redacted = PHONE_REGEX.sub("[REDACTED_PHONE]", redacted)

        return redacted
