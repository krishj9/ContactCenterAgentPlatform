"""Data Quality: PII Leakage Check (P3.11).

Scans authored policies, FAQ data, and evaluation qrels for unredacted
Social Security Numbers (SSN) and Primary Account Numbers (PAN / credit cards).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure repo root and backend in sys.path
repo_root = Path(__file__).resolve().parent.parent.parent

SSN_REGEX = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")
CARD_PAN_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")


def luhn_checksum_valid(card_number_str: str) -> bool:
    """Validate Luhn checksum for 16-digit card numbers (ignoring obvious test placeholders)."""
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) != 16:
        return False
    # Ignore obvious dummy sequences
    if len(set(digits)) == 1:
        return False
    if digits == list(range(1, 10)) + list(range(1, 8)):
        return False

    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


def scan_file_for_pii(filepath: Path) -> list[str]:
    """Scan single file for potential PII violations."""
    findings: list[str] = []
    text = filepath.read_text(encoding="utf-8")

    # Check SSN
    ssn_matches = SSN_REGEX.findall(text)
    if ssn_matches:
        findings.append(f"SSN pattern detected: {ssn_matches}")

    # Check Credit Card numbers with Luhn
    card_matches = CARD_PAN_REGEX.findall(text)
    for match in card_matches:
        clean = match.replace(" ", "").replace("-", "")
        # Filter out 1-800 phone numbers or toll-free numbers like 1-800-555-CARD
        if luhn_checksum_valid(clean):
            findings.append(f"Valid card PAN checksum detected: {match}")

    return findings


def assert_zero_pii(target_dirs: list[Path] | None = None) -> None:
    """Verify zero unredacted PII across corpus files."""
    target_dirs = target_dirs or [repo_root / "corpora" / "policy"]
    violations: list[str] = []

    for directory in target_dirs:
        for fpath in directory.glob("**/*"):
            if fpath.is_file() and fpath.suffix in (".md", ".json", ".csv", ".jsonl"):
                findings = scan_file_for_pii(fpath)
                for f in findings:
                    violations.append(f"{fpath.name}: {f}")

    if violations:
        msg = f"❌ PII Detection Check FAILED: {len(violations)} violations found:\n"
        for v in violations:
            msg += f"  - {v}\n"
        raise AssertionError(msg)

    print("✅ PII Detection Check PASSED: Zero unredacted SSN/PAN patterns detected.")


def main() -> None:
    try:
        assert_zero_pii()
    except AssertionError as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
