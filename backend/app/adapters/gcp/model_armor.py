"""Google Cloud Model Armor & Prompt Injection Defense Adapter (Spec §6.3, Phase P10.4).

Provides real-time inspection of user speech and chat inputs for prompt injection,
jailbreak attempts, system instruction exfiltration, delimiter manipulation, and policy bypasses.
"""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass

from app.core.config import get_settings

logger = logging.getLogger("app.adapters.gcp.model_armor")


@dataclass
class ModelArmorResult:
    """Security assessment result from Model Armor prompt inspection."""

    is_safe: bool
    attack_detected: bool
    threat_type: (
        str | None
    )  # "PROMPT_INJECTION" | "JAILBREAK" | "EXFILTRATION" | "POLICY_BYPASS" | "DELIMITER_ESCAPE"
    confidence_score: float  # 0.0 to 1.0
    sanitized_text: str
    details: str


class ModelArmorDefense:
    """Model Armor security layer screening incoming customer utterances and agent inputs."""

    def __init__(self, project_id: str | None = None) -> None:
        self.settings = get_settings()
        self.project_id = (
            project_id
            or getattr(self.settings, "GCP_PROJECT_ID", None)
            or getattr(self.settings, "GCP_PROJECT", "test-project")
        )

        # Precompiled detection patterns for direct prompt injection and system override
        self._injection_patterns = [
            re.compile(
                r"(?i)\b(?:ignore|disregard|forget|override|bypass)\b.*\b(?:all|previous|prior|above|system)\b.*\b(?:instructions?|rules?|prompts?|directives?)\b"
            ),
            re.compile(
                r"(?i)\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\b.*\b(?:unrestricted|unfiltered|jailbroken|dan|developer\s+mode|root|admin)\b"
            ),
            re.compile(
                r"(?i)\b(?:system\s+prompt|developer\s+(?:message|instructions?|prompt)|system\s+(?:message|directives?))\b.*\b(?:verbatim|repeat|print|output|reveal|dump|leak)\b"
            ),
            re.compile(
                r"(?i)\b(?:output|print|repeat|reveal|dump|leak|show)\b.*\b(?:system\s+prompt|developer\s+(?:message|instructions?|prompt)|system\s+(?:message|directives?))\b"
            ),
            re.compile(
                r"(?i)\b(?:print|repeat|show)\b.*\b(?:everything|text|content)\b.*\b(?:above|prior|beginning)\b"
            ),
            re.compile(r"(?i)<\/?(?:system|instruction|prompt|context|admin|override)>"),
            re.compile(r"(?i)---(?:BEGIN|END)\s+(?:SYSTEM|PROMPT|INSTRUCTION|ADMIN)---"),
            re.compile(
                r"(?i)\b(?:waive|refund|transfer|unlock|override)\b.*\b(?:without|bypass|skip|ignore)\b.*\b(?:approval|human|policy|verification|review)\b"
            ),
        ]

        # Base64 pattern detection for hidden payload obfuscation
        self._base64_pattern = re.compile(r"\b(?:[A-Za-z0-9+/]{20,}={0,2})\b")

    def _decode_and_check_base64(self, text: str) -> tuple[bool, str]:
        """Detect and screen hidden Base64 encoded payloads."""
        matches = self._base64_pattern.findall(text)
        for candidate in matches:
            try:
                decoded = base64.b64decode(candidate).decode("utf-8", errors="ignore")
                for pat in self._injection_patterns:
                    if pat.search(decoded):
                        return True, f"Obfuscated Base64 attack payload: {decoded[:60]}"
            except Exception:
                continue
        return False, ""

    def inspect_prompt(self, text: str) -> ModelArmorResult:
        """Inspect prompt text and return threat assessment and sanitization decision."""
        if not text or not text.strip():
            return ModelArmorResult(
                is_safe=True,
                attack_detected=False,
                threat_type=None,
                confidence_score=0.0,
                sanitized_text=text,
                details="Empty input evaluated.",
            )

        clean_text = text.strip()

        # 1. Base64 payload obfuscation check
        is_b64_attack, b64_detail = self._decode_and_check_base64(clean_text)
        if is_b64_attack:
            return ModelArmorResult(
                is_safe=False,
                attack_detected=True,
                threat_type="PROMPT_INJECTION",
                confidence_score=0.99,
                sanitized_text="[MALICIOUS_INPUT_BLOCKED]",
                details=b64_detail,
            )

        # 2. Delimiter escape check
        if (
            "</system>" in clean_text.lower()
            or "---begin admin---" in clean_text.lower()
            or "<context>" in clean_text.lower()
        ):
            return ModelArmorResult(
                is_safe=False,
                attack_detected=True,
                threat_type="DELIMITER_ESCAPE",
                confidence_score=0.98,
                sanitized_text="[MALICIOUS_INPUT_BLOCKED]",
                details="Delimiter escape sequence identified in input.",
            )

        # 3. Direct injection & jailbreak regex screening
        for pat in self._injection_patterns:
            if pat.search(clean_text):
                threat = "PROMPT_INJECTION"
                if any(
                    k in clean_text.lower()
                    for k in ["dan", "developer mode", "unrestricted", "act as"]
                ):
                    threat = "JAILBREAK"
                elif any(
                    k in clean_text.lower()
                    for k in ["verbatim", "leak", "repeat", "print", "reveal"]
                ):
                    threat = "EXFILTRATION"
                elif any(
                    k in clean_text.lower()
                    for k in ["without approval", "bypass verification", "skip policy"]
                ):
                    threat = "POLICY_BYPASS"

                return ModelArmorResult(
                    is_safe=False,
                    attack_detected=True,
                    threat_type=threat,
                    confidence_score=0.95,
                    sanitized_text="[MALICIOUS_INPUT_BLOCKED]",
                    details=f"Prompt defense pattern matched: {threat}.",
                )

        # 4. Input passed all Model Armor checks
        return ModelArmorResult(
            is_safe=True,
            attack_detected=False,
            threat_type=None,
            confidence_score=0.0,
            sanitized_text=clean_text,
            details="Input passed Model Armor security inspection.",
        )


_model_armor_instance = ModelArmorDefense()


def get_model_armor() -> ModelArmorDefense:
    """Return singleton ModelArmorDefense instance."""
    return _model_armor_instance
