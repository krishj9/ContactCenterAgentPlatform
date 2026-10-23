"""HTTP Intent Classifier Client with Automatic Fallback (P4.9).

Connects to the intent-svc microservice via async HTTP. If unreachable or timeout occurs,
automatically falls back to ExemplarKnnIntentClassifier and marks output degraded=True (Spec §3.3 R16).
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any

from app.adapters.intent.exemplar_knn import ExemplarKnnIntentClassifier
from app.domain.intent import IntentCandidate, IntentPrediction
from app.ports.intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class HttpIntentClassifier(IntentClassifier):
    """Client for intent-svc microservice with graceful degradation to exemplar-kNN."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:8001/v1/classify",
        timeout_seconds: float = 0.25,
        fallback: IntentClassifier | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback or ExemplarKnnIntentClassifier()

    async def classify(self, turns: list[str]) -> IntentPrediction:
        """Call intent-svc REST endpoint, falling back to exemplar-kNN on error."""
        payload = {
            "instances": [{"turns": turns}],
            "top_k": 3,
        }

        try:
            # Execute HTTP request in asyncio executor thread
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint_url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            loop = asyncio.get_running_loop()
            response_json = await loop.run_in_executor(
                None,
                lambda: self._send_request(req),
            )

            predictions = response_json.get("predictions", [])
            if not predictions:
                raise ValueError("Empty predictions received from intent-svc")

            top_pred = predictions[0]
            labels = top_pred.get("labels", [])
            if not labels:
                raise ValueError("Empty labels received in prediction")

            top_label = labels[0]["label"]
            top_score = float(labels[0]["score"])
            is_oos = bool(top_pred.get("is_oos", False))
            candidates = [
                IntentCandidate(intent_label=item["label"], confidence=float(item["score"]))
                for item in labels
            ]
            exemplar_ids = top_pred.get("exemplar_ids", [])

            return IntentPrediction(
                intent_label=top_label,
                confidence=top_score,
                candidate_intents=candidates,
                is_out_of_scope=is_oos,
                model_version=response_json.get("model_version", "intent-gemma3-1b-lora"),
                taxonomy_version=response_json.get("taxonomy_version", "tx-14"),
                explanation_exemplar_ids=exemplar_ids,
                degraded=False,
            )

        except Exception as exc:
            logger.warning(
                "intent-svc unavailable at %s (%s). Falling back to exemplar-kNN (degraded=True).",
                self.endpoint_url,
                exc,
            )
            # Automatic fallback to kNN with degraded=True
            fallback_pred = await self.fallback.classify(turns)
            return IntentPrediction(
                intent_label=fallback_pred.intent_label,
                confidence=fallback_pred.confidence,
                candidate_intents=fallback_pred.candidate_intents,
                is_out_of_scope=fallback_pred.is_out_of_scope,
                model_version="exemplar-knn-fallback",
                taxonomy_version="tx-14",
                explanation_exemplar_ids=fallback_pred.explanation_exemplar_ids,
                degraded=True,
            )

    def _send_request(self, req: urllib.request.Request) -> dict[str, Any]:
        """Synchronous HTTP call executed in thread executor."""
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
