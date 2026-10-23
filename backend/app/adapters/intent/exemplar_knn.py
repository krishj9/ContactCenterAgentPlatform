"""Exemplar-kNN Intent Classifier Adapter (Spec §3.2.1, P4.9).

Fallback classifier and explainability engine indexing training exemplars.
Returns nearest training utterances for explainability ("Why did the model pick this?").
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.domain.intent import IntentCandidate, IntentPrediction
from app.ports.intent_classifier import IntentClassifier


def _tokenize(text: str) -> list[str]:
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in clean.split() if len(w) >= 2]
    feats = list(words)
    for i in range(len(words) - 1):
        feats.append(f"{words[i]}_{words[i + 1]}")
    return feats


class ExemplarKnnIntentClassifier(IntentClassifier):
    """Exemplar k-NN classifier providing explainability citations and fallback."""

    def __init__(
        self,
        exemplars_path: Path | str | None = None,
        k: int = 5,
        default_intent: str = "card_declined",
    ) -> None:
        self.k = k
        self.default_intent = default_intent
        self.doc_ids: list[str] = []
        self.doc_texts: list[str] = []
        self.doc_labels: list[str] = []
        self.idf: dict[str, float] = {}
        self.doc_vectors: list[dict[str, float]] = []
        self.doc_norms: list[float] = []

        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        meta_path = repo_root / "ml" / "intent" / "artifacts" / "model_metadata.json"
        self._engine: Any = None
        if meta_path.exists():
            try:
                from ml.intent.export import Int8IntentServingEngine

                self._engine = Int8IntentServingEngine(meta_path)
            except Exception:
                self._engine = None

        # Find exemplar index path
        if exemplars_path:
            p = Path(exemplars_path)
        else:
            p = repo_root / "ml" / "intent" / "artifacts" / "exemplar_index.json"

        self.exemplars_by_label: dict[str, list[dict[str, Any]]] = {}
        if p.exists():
            with open(p, encoding="utf-8") as f:
                self.exemplars_by_label = json.load(f)
            self._build_index()
        else:
            self._build_default_index()

    def _build_index(self) -> None:
        """Index loaded exemplars into inverted TF-IDF matrix."""
        records: list[dict[str, Any]] = []
        for label, ex_list in self.exemplars_by_label.items():
            for ex in ex_list:
                records.append(
                    {
                        "id": ex.get("id", f"ex-{label}"),
                        "text": ex.get("text", ""),
                        "label": label,
                    }
                )

        self._fit_records(records)

    def _build_default_index(self) -> None:
        """Seed minimal baseline exemplars for offline test stability."""
        seed_records = [
            {
                "id": "ex-card_declined-1",
                "text": "my card was declined at checkout",
                "label": "card_declined",
            },
            {
                "id": "ex-card_declined-2",
                "text": "can you clear the block on my card?",
                "label": "card_declined",
            },
            {
                "id": "ex-travel_notice-1",
                "text": "i am traveling abroad next week",
                "label": "travel_notice",
            },
            {
                "id": "ex-travel_notice-2",
                "text": "put a travel notice on my sapphire card for tokyo",
                "label": "travel_notice",
            },
            {
                "id": "ex-fee_dispute-1",
                "text": "i want this overdraft fee waived from my statement",
                "label": "fee_dispute",
            },
            {
                "id": "ex-fee_dispute-2",
                "text": "will the thirty-five dollar fee be refunded?",
                "label": "fee_dispute",
            },
            {
                "id": "ex-lost_or_stolen_card-1",
                "text": "i left my wallet on the commuter train",
                "label": "lost_or_stolen_card",
            },
            {
                "id": "ex-charged_twice-1",
                "text": "i was charged twice for the same hotel booking",
                "label": "charged_twice",
            },
            {
                "id": "ex-out_of_scope-1",
                "text": "what is the weather like in new york?",
                "label": "out_of_scope",
            },
            {
                "id": "ex-out_of_scope-2",
                "text": "can you give me a recipe for sourdough bread?",
                "label": "out_of_scope",
            },
        ]
        self._fit_records(seed_records)

    def _fit_records(self, records: list[dict[str, Any]]) -> None:
        doc_count = len(records)
        df: Counter[str] = Counter()

        self.doc_ids = [r["id"] for r in records]
        self.doc_texts = [r["text"] for r in records]
        self.doc_labels = [r["label"] for r in records]

        all_tokens = [_tokenize(r["text"]) for r in records]
        for tokens in all_tokens:
            for t in set(tokens):
                df[t] += 1

        self.idf = {t: math.log((doc_count + 1) / (c + 1)) + 1.0 for t, c in df.items()}

        self.doc_vectors = []
        self.doc_norms = []
        for tokens in all_tokens:
            tf = Counter(tokens)
            vec = {t: (1.0 + math.log(c)) * self.idf.get(t, 1.0) for t, c in tf.items()}
            norm_sq = sum(v * v for v in vec.values())
            self.doc_vectors.append(vec)
            self.doc_norms.append(math.sqrt(norm_sq) if norm_sq > 0 else 1.0)

    async def classify(self, turns: list[str]) -> IntentPrediction:
        """Classify customer turns using serving engine or exemplar k-NN matching."""
        if self._engine is not None:
            pred = self._engine.classify_turns(turns)
            top_label = pred.labels[0]["label"] if pred.labels else self.default_intent
            top_score = pred.labels[0]["score"] if pred.labels else 0.70
            candidates = [
                IntentCandidate(intent_label=item["label"], confidence=item["score"])
                for item in pred.labels
            ]
            return IntentPrediction(
                intent_label=top_label,
                confidence=top_score,
                candidate_intents=candidates,
                is_out_of_scope=pred.is_oos,
                explanation_exemplar_ids=pred.exemplar_ids,
                degraded=True,
            )

        joined = " [TURN] ".join(turns)
        tokens = _tokenize(joined)

        if not tokens or not self.doc_vectors:
            return IntentPrediction(
                intent_label=self.default_intent,
                confidence=0.75,
                degraded=True,
            )

        # Build query vector
        q_tf = Counter(tokens)
        q_vec = {t: (1.0 + math.log(c)) * self.idf.get(t, 1.0) for t, c in q_tf.items()}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        # Compute cosine similarities
        scores: list[tuple[int, float]] = []
        for doc_idx, doc_vec in enumerate(self.doc_vectors):
            dot = sum(q_val * doc_vec.get(t, 0.0) for t, q_val in q_vec.items())
            if dot > 0:
                sim = dot / (q_norm * self.doc_norms[doc_idx])
                scores.append((doc_idx, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = scores[: self.k]

        if not top_matches:
            return IntentPrediction(
                intent_label=self.default_intent,
                confidence=0.60,
                is_out_of_scope=False,
                degraded=True,
            )

        # Weighted label vote
        votes: dict[str, float] = defaultdict(float)
        exemplar_ids: list[str] = []
        for doc_idx, sim in top_matches:
            lbl = self.doc_labels[doc_idx]
            votes[lbl] += max(0.01, sim)
            if len(exemplar_ids) < 3:
                exemplar_ids.append(self.doc_ids[doc_idx])

        total_votes = sum(votes.values())
        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)

        top_label, top_score = sorted_votes[0]
        confidence = min(0.99, top_score / total_votes) if total_votes > 0 else 0.70

        candidates = [
            IntentCandidate(intent_label=lbl, confidence=round(score / total_votes, 4))
            for lbl, score in sorted_votes[:3]
        ]

        is_oos = (top_label == "out_of_scope") or (confidence < 0.55)

        return IntentPrediction(
            intent_label=top_label,
            confidence=round(confidence, 4),
            candidate_intents=candidates,
            is_out_of_scope=is_oos,
            explanation_exemplar_ids=exemplar_ids,
            degraded=True,
        )
