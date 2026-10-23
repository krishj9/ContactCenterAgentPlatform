import urllib.error
from unittest.mock import patch

import pytest

from app.adapters.intent.client import HttpIntentClassifier
from app.adapters.intent.exemplar_knn import ExemplarKnnIntentClassifier
from app.domain.intent import IntentPrediction


@pytest.mark.asyncio
async def test_exemplar_knn_intent_classifier():
    """Verify that ExemplarKnnIntentClassifier indexes exemplars and returns predictions."""
    classifier = ExemplarKnnIntentClassifier()
    pred: IntentPrediction = await classifier.classify(
        ["my card was declined at checkout", "clear the block"]
    )

    assert pred.intent_label == "card_declined"
    assert pred.confidence > 0.50
    assert pred.degraded is True
    assert len(pred.explanation_exemplar_ids) > 0
    assert len(pred.candidate_intents) > 0


@pytest.mark.asyncio
async def test_exemplar_knn_out_of_scope():
    """Verify that out of scope queries return is_out_of_scope=True."""
    classifier = ExemplarKnnIntentClassifier()
    pred: IntentPrediction = await classifier.classify(["what is the weather like in tokyo?"])

    assert pred.is_out_of_scope is True
    assert pred.intent_label == "out_of_scope"
    assert pred.degraded is True


@pytest.mark.asyncio
async def test_http_intent_classifier_fallback_on_unreachable():
    """Verify that HttpIntentClassifier gracefully falls back to k-NN (degraded=True) when server is unreachable."""
    fallback_knn = ExemplarKnnIntentClassifier()
    client = HttpIntentClassifier(
        endpoint_url="http://127.0.0.1:59999/v1/classify",
        timeout_seconds=0.1,
        fallback=fallback_knn,
    )

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        pred: IntentPrediction = await client.classify(["my card was declined at checkout"])

    assert pred.degraded is True
    assert pred.intent_label == "card_declined"
    assert pred.model_version == "exemplar-knn-fallback"
