"""Unit tests for TranscriptReplayRunner across golden scenario fixtures."""

from pathlib import Path

import pytest

from app.contracts.events_v1 import (
    GroundingStatus,
    GuardrailAlertEvent,
    SummaryReadyEvent,
)
from app.core.container import Container
from app.eval.replay_runner import TranscriptReplayRunner

SCENARIOS_DIR = Path("eval/scenarios")


@pytest.mark.asyncio
async def test_replay_card_declined_scenario():
    container = Container()
    runner = TranscriptReplayRunner(container)

    scenario_path = SCENARIOS_DIR / "card_declined.json"
    result = await runner.replay_scenario(scenario_path)

    assert result.scenario_id == "card_declined"
    assert result.turns_replayed == 4
    assert result.total_events > 5

    # Verify event types emitted in sequence
    event_types = [e.type for e in result.events_emitted]
    assert event_types[0] == "session.ready"
    assert "transcript.final" in event_types
    assert "issue.update" in event_types
    assert "assist.recommendation" in event_types
    assert event_types[-1] == "summary.ready"

    # Verify intent prediction
    assert "card_declined" in result.predicted_intents
    assert GroundingStatus.GROUNDED in result.grounding_states


@pytest.mark.asyncio
async def test_replay_out_of_scope_chit_chat_weather():
    """Verify that OOS chit-chat triggers GuardrailAlertEvent and suppresses assist."""
    container = Container()
    runner = TranscriptReplayRunner(container)

    scenario_path = SCENARIOS_DIR / "chit_chat_weather.json"
    result = await runner.replay_scenario(scenario_path)

    assert result.scenario_id == "chit_chat_weather"
    assert "out_of_scope" in result.predicted_intents

    # Verify GuardrailAlertEvent emitted
    alerts = [e for e in result.events_emitted if isinstance(e, GuardrailAlertEvent)]
    assert len(alerts) > 0
    assert alerts[0].code == "OUT_OF_SCOPE"
    assert GroundingStatus.MISSING_EVIDENCE in result.grounding_states


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename",
    [
        "fee_dispute.json",
        "travel_notice.json",
        "lost_card.json",
        "charged_twice.json",
        "chit_chat_recipe.json",
    ],
)
async def test_replay_all_remaining_scenarios(filename: str) -> None:

    container = Container()
    runner = TranscriptReplayRunner(container)

    scenario_path = SCENARIOS_DIR / filename
    result = await runner.replay_scenario(scenario_path)

    assert result.turns_replayed >= 2
    assert result.total_events >= 4
    assert any(isinstance(e, SummaryReadyEvent) for e in result.events_emitted)


@pytest.mark.asyncio
async def test_replay_golden_scenario_with_gcp_profile():
    """Verify golden scenario replay runs end-to-end with APP_PROFILE=gcp (Spec P7 exit criteria)."""
    from app.core.config import Settings

    settings = Settings(
        APP_PROFILE="gcp",
        GCP_PROJECT="test-gcp-project",
        GCP_REGION="us-central1",
    )
    container = Container(settings=settings)
    runner = TranscriptReplayRunner(container)

    scenario_path = SCENARIOS_DIR / "card_declined.json"
    result = await runner.replay_scenario(scenario_path)

    assert result.scenario_id == "card_declined"
    assert result.turns_replayed == 4
    assert result.total_events > 5
    assert any(isinstance(e, SummaryReadyEvent) for e in result.events_emitted)
    assert "card_declined" in result.predicted_intents
