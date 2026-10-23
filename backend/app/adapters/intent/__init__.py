"""Intent classification adapters."""

from app.adapters.intent.client import HttpIntentClassifier
from app.adapters.intent.exemplar_knn import ExemplarKnnIntentClassifier

__all__ = ["HttpIntentClassifier", "ExemplarKnnIntentClassifier"]
