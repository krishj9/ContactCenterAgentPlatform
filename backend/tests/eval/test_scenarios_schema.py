"""Unit tests validating golden scenario fixtures against ScenarioFixture schema."""

import json
from pathlib import Path

import pytest
from eval.schema import ScenarioFixture

SCENARIOS_DIR = Path("eval/scenarios")

REQUIRED_SCENARIO_FILES = [
    "card_declined.json",
    "fee_dispute.json",
    "travel_notice.json",
    "lost_card.json",
    "charged_twice.json",
    "chit_chat_weather.json",
    "chit_chat_recipe.json",
]


def test_required_scenario_files_exist():
    """Verify all 7 required scenario fixtures exist on disk."""
    assert SCENARIOS_DIR.exists(), f"Directory {SCENARIOS_DIR} does not exist"
    for filename in REQUIRED_SCENARIO_FILES:
        path = SCENARIOS_DIR / filename
        assert path.exists(), f"Scenario fixture {filename} missing at {path}"


@pytest.mark.parametrize("filename", REQUIRED_SCENARIO_FILES)
def test_scenario_validates_against_schema(filename: str):
    """Validate each scenario JSON against Pydantic ScenarioFixture schema."""
    path = SCENARIOS_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    fixture = ScenarioFixture.model_validate(data)
    assert fixture.scenario_id
    assert len(fixture.turns) >= 2
    assert fixture.customer_profile.name

    # Verify at least one customer turn has an expected intent
    customer_turns = [t for t in fixture.turns if t.speaker == "customer"]
    assert len(customer_turns) > 0
    assert any(t.expected_intent is not None for t in customer_turns)
