"""Unit tests for pipeline data quality assertions (P3.11)."""

from __future__ import annotations

from pathlib import Path

from pipeline.quality.coverage_check import assert_policy_coverage
from pipeline.quality.pii_check import assert_zero_pii, luhn_checksum_valid


def test_coverage_assertion_passes_for_corpus() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    policy_dir = repo_root / "corpora" / "policy"
    # Should not raise
    assert_policy_coverage(policy_dir)


def test_pii_check_passes_for_corpus() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    # Should not raise
    assert_zero_pii([repo_root / "corpora" / "policy"])


def test_luhn_checksum_helper() -> None:
    # Test valid vs invalid card numbers
    assert not luhn_checksum_valid("0000000000000000")  # Repeated digits filtered
    assert not luhn_checksum_valid("123456781234567")  # 15 digits
    assert not luhn_checksum_valid("1234567890123456")  # Invalid checksum
