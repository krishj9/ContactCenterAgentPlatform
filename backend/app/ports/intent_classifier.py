"""Port protocol for fast-path intent classification."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.intent import IntentPrediction


@runtime_checkable
class IntentClassifier(Protocol):
    """Protocol for intent classification services."""

    async def classify(self, turns: list[str]) -> IntentPrediction:
        """Classify customer utterance turns into an intent hypothesis."""
        ...
