"""Unit tests for TaxonomyRegistry and aliases (P3.1)."""

from __future__ import annotations

from pipeline.taxonomy import TaxonomyRegistry


def test_taxonomy_loads_successfully() -> None:
    registry = TaxonomyRegistry()
    assert len(registry.list_all_intents()) >= 80
    assert registry.version == "tx-14"


def test_policy_required_intents() -> None:
    registry = TaxonomyRegistry()
    required = registry.list_policy_required_intents()
    assert len(required) == 14
    assert "card_declined" in required
    assert "travel_notice" in required
    assert "fee_dispute" in required
    assert "fraud_report" in required
    assert "pin_blocked" in required
    assert "cancel_transfer" in required


def test_alias_resolution() -> None:
    registry = TaxonomyRegistry()
    # Direct match
    assert registry.resolve_alias("card_declined") == "card_declined"

    # Alias matches
    assert registry.resolve_alias("card rejected") == "card_declined"
    assert registry.resolve_alias("unauthorized charge") == "fraud_report"
    assert registry.resolve_alias("traveling abroad") == "travel_notice"
    assert registry.resolve_alias("waive fee") == "fee_dispute"
    assert registry.resolve_alias("stolen card") == "lost_or_stolen_card"
    assert registry.resolve_alias("locked out of atm pin") == "pin_blocked"


def test_taxonomy_validation_passes() -> None:
    registry = TaxonomyRegistry()
    errors = registry.validate()
    assert errors == []
