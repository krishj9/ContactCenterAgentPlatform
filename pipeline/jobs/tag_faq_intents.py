"""FAQ Intent Tagging Job (P3.5).

Semantically links FAQ question-answer pairs to canonical taxonomy intent labels,
generating corpora/faq_intent_tags.csv.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from pipeline.taxonomy import TaxonomyRegistry

repo_root = Path(__file__).resolve().parent.parent.parent


def tokenize(text: str) -> set[str]:
    """Extract normalized alphanumeric word tokens."""
    return set(re.findall(r"\b[a-z0-9_]{3,}\b", text.lower()))


class FAQIntentTagger:
    """Keyword and token similarity tagger matching FAQs to canonical intents."""

    def __init__(self, taxonomy: TaxonomyRegistry) -> None:
        self.taxonomy = taxonomy
        self._intents = taxonomy.list_all_intents()

        # Build feature token sets per intent
        self._intent_features: dict[str, set[str]] = {}
        for intent in self._intents:
            features = tokenize(f"{intent.label} {intent.display_name} {intent.description}")
            # Add intent label words
            features.update(intent.label.lower().split("_"))
            self._intent_features[intent.label] = features

        # Specific high-priority keyword overrides for banking terminology
        self._keyword_rules: list[tuple[list[str], str, float]] = [
            (
                ["decline", "declined", "declining", "failed payment", "transaction failed"],
                "card_declined",
                0.95,
            ),
            (["travel", "abroad", "foreign", "overseas", "itinerary"], "travel_notice", 0.95),
            (["fee", "charges", "annual fee", "surcharge", "overdraft fee"], "fee_dispute", 0.90),
            (
                ["fraud", "unauthorized", "suspicious transaction", "scam", "skimming"],
                "fraud_report",
                0.95,
            ),
            (
                ["charged twice", "duplicate transaction", "double charge", "billed twice"],
                "charged_twice",
                0.95,
            ),
            (["refund", "merchant refund", "return credit"], "Refund_not_showing_up", 0.90),
            (
                ["lost card", "stolen card", "lost my card", "misplaced card"],
                "lost_or_stolen_card",
                0.95,
            ),
            (["compromised card", "compromised", "cloned card"], "compromised_card", 0.95),
            (
                [
                    "card arrival",
                    "delivery status",
                    "dispatch card",
                    "tracking card",
                    "receive card",
                ],
                "card_arrival",
                0.90,
            ),
            (
                ["order physical card", "new card", "replace card", "card replacement"],
                "order_physical_card",
                0.90,
            ),
            (
                [
                    "pin blocked",
                    "locked pin",
                    "pin lockout",
                    "forgot pin",
                    "unblock pin",
                    "reset pin",
                ],
                "pin_blocked",
                0.95,
            ),
            (
                ["cancel transfer", "recall wire", "stop payment", "cancel wire"],
                "cancel_transfer",
                0.95,
            ),
            (
                ["transfer", "wire transfer", "send money", "neft", "rtgs", "imps"],
                "transfer_into_account",
                0.85,
            ),
            (
                ["balance", "account balance", "statement", "mini statement"],
                "balance_not_updated_after_cheque_or_cash_deposit",
                0.80,
            ),
            (["activate", "activation", "card active"], "activate_my_card", 0.90),
            (
                ["direct debit", "standing instruction", "auto debit"],
                "direct_debit_payment_not_recognised",
                0.85,
            ),
        ]

    def tag_question(self, question: str, category: str = "") -> tuple[str, float]:
        """Assign best canonical intent label with confidence score."""
        q_lower = question.lower()
        q_tokens = tokenize(f"{question} {category}")

        # 1. Check keyword rules
        for keywords, intent_label, conf in self._keyword_rules:
            if any(kw in q_lower for kw in keywords):
                return intent_label, conf

        # 2. Check Jaccard / token overlap with intent descriptions
        best_intent = "out_of_scope"
        best_score = 0.0

        for intent in self._intents:
            intent_label = intent.label
            intent_tokens = self._intent_features[intent_label]
            intersection = q_tokens.intersection(intent_tokens)
            if not intersection:
                continue
            # Jaccard score weighted by question token coverage
            score = len(intersection) / (len(q_tokens) + 1)
            if score > best_score:
                best_score = score
                best_intent = intent_label

        if best_score >= 0.25:
            conf = min(0.85, 0.40 + best_score)
            return best_intent, round(conf, 2)

        return "out_of_scope", 0.30


def run_tagging(
    faq_input_path: Path | None = None,
    output_csv_path: Path | None = None,
) -> Path:
    """Run FAQ tagging and write CSV."""
    faq_input_path = (
        faq_input_path
        or repo_root / "data" / "processed" / "normalized" / "faq" / "faq.normalized.jsonl"
    )
    output_csv_path = output_csv_path or repo_root / "corpora" / "faq_intent_tags.csv"

    if not faq_input_path.exists():
        # Fallback to raw csv if normalized does not exist
        raw_csv = repo_root / "data" / "raw" / "faq" / "BankFAQs.csv"
        if not raw_csv.exists():
            raise FileNotFoundError(f"Neither {faq_input_path} nor {raw_csv} found.")

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    taxonomy = TaxonomyRegistry()
    tagger = FAQIntentTagger(taxonomy)

    records: list[dict[str, Any]] = []

    if faq_input_path.exists():
        with open(faq_input_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                records.append(
                    {
                        "id": data.get("id"),
                        "question": data.get("title", ""),
                        "category": data.get("metadata", {}).get("category", "general"),
                    }
                )
    else:
        raw_csv = repo_root / "data" / "raw" / "faq" / "BankFAQs.csv"
        with open(raw_csv, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                records.append(
                    {
                        "id": f"bankfaqs-general-{idx}",
                        "question": row.get("Question") or row.get("question") or "",
                        "category": row.get("Category") or row.get("category") or "general",
                    }
                )

    tagged_rows: list[dict[str, Any]] = []
    distribution: Counter[str] = Counter()

    for rec in records:
        faq_id = rec["id"]
        question = rec["question"]
        category = rec["category"]

        intent, conf = tagger.tag_question(question, category)
        distribution[intent] += 1

        review_status = "auto_accepted" if conf >= 0.80 else "reviewed"

        tagged_rows.append(
            {
                "faq_id": faq_id,
                "question": question,
                "category": category,
                "assigned_intent": intent,
                "confidence": f"{conf:.2f}",
                "review_status": review_status,
            }
        )

    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "faq_id",
            "question",
            "category",
            "assigned_intent",
            "confidence",
            "review_status",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tagged_rows)

    print(f"✅ Tagged {len(tagged_rows)} FAQs -> {output_csv_path}")
    print(f"Top 10 assigned intents: {distribution.most_common(10)}")

    return output_csv_path


if __name__ == "__main__":
    run_tagging()
