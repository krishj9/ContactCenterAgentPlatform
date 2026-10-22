"""Test adapter for IntentClassifier port."""

from __future__ import annotations

from app.domain.intent import IntentCandidate, IntentPrediction


class TestIntentClassifier:
    """In-memory deterministic intent classifier for test and replay environments."""

    __test__ = False

    def __init__(self, default_intent: str = "card_declined") -> None:
        self.default_intent = default_intent

    async def classify(self, turns: list[str]) -> IntentPrediction:
        joined = " ".join(turns).lower()

        if any(w in joined for w in ["weather", "snow", "rain", "recipe", "yeast", "cookie"]):
            return IntentPrediction(
                intent_label="out_of_scope",
                confidence=0.92,
                is_out_of_scope=True,
                candidate_intents=[IntentCandidate("out_of_scope", 0.92)],
            )

        if "decline" in joined or "declined" in joined or "checkout" in joined:
            label = "card_declined"
        elif "fee" in joined or "overdraft" in joined or "waive" in joined:
            label = "fee_dispute"
        elif "travel" in joined or "tokyo" in joined or "abroad" in joined:
            label = "travel_notice"
        elif "lost" in joined or "wallet" in joined or "stolen" in joined:
            label = "lost_card"
        elif "twice" in joined or "duplicate" in joined or "hotel" in joined:
            label = "charged_twice"
        else:
            label = self.default_intent

        return IntentPrediction(
            intent_label=label,
            confidence=0.95,
            is_out_of_scope=False,
            candidate_intents=[
                IntentCandidate(label, 0.95),
                IntentCandidate("general_inquiry", 0.05),
            ],
            explanation_exemplar_ids=[f"ex-{label}-1", f"ex-{label}-2"],
        )
