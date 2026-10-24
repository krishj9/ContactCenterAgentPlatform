"""Dataset Preparation for Intent Classifier (P4.1).

Prepares stratified train/validation/test splits from Banking77, injects CLINC150
out-of-scope (OOS) utterances, conversational filler chit-chat, and golden scenario fixtures.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Ensure workspace root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline.taxonomy import TaxonomyRegistry

OOS_UTTERANCES = [
    # General Chit-Chat & Greetings
    "hi can you hear me ok?",
    "hello is anybody there?",
    "good morning how are you doing today?",
    "what's the weather like in new york right now?",
    "can you tell me a good recipe for sourdough bread?",
    "who won the world series last year?",
    "i was wondering if you know any good movies playing this weekend",
    "can you help me with my math homework?",
    "what time is sunset in tokyo?",
    "tell me a funny joke",
    "how do i fix a flat bicycle tire?",
    "can you recommend a good book to read on vacation?",
    "what is the capital of australia?",
    "what's the score in the lakers game?",
    "do you like working at this bank?",
    "is it going to rain this afternoon?",
    "can you translate this phrase into spanish for me?",
    "what temperature should i cook chicken breast to?",
    "tell me about quantum computing",
    "how far is the moon from the earth?",
    # Conversational Disfluencies & Hesitations without intent
    "um wait a second let me find my papers",
    "uh hello sorry wrong number i think",
    "hang on my dog is barking",
    "sorry i was on mute what did you say?",
    "let me call you right back",
    "testing one two three",
    "pardon me i couldn't hear that",
    "just checking if the line is working",
    "i'm sorry my connection is really bad",
    "can you speak a little louder please?",
    # Non-banking service requests
    "can i order a pizza through this service?",
    "how do i reset my netflix password?",
    "where is the nearest gas station to 5th avenue?",
    "can you check my flight status on united?",
    "what are your store hours for the grocery branch?",
    "can you help me set up my new iphone?",
    "how do i clean coffee out of a white shirt?",
    "what's the exchange rate between bitcoin and dogecoin?",
    "is mercury in retrograde right now?",
    "can you book an uber for me please?",
]


def load_banking77(path: Path) -> list[dict[str, str]]:
    """Load Banking77 CSV file with columns: text, category."""
    if not path.exists():
        raise FileNotFoundError(f"Banking77 file not found at {path}")

    records: list[dict[str, str]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = (row.get("text") or "").strip()
            cat = (row.get("category") or "").strip()
            if text and cat:
                records.append({"text": text, "category": cat})
    return records


def load_golden_scenarios(scenarios_dir: Path, taxonomy: TaxonomyRegistry) -> list[dict[str, Any]]:
    """Extract all customer turns and expected intents from golden scenario fixtures."""
    scenario_records: list[dict[str, Any]] = []
    for file in sorted(scenarios_dir.glob("*.json")):
        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        scenario_id = data.get("scenario_id", file.stem)
        customer_history: list[str] = []
        for turn in data.get("turns", []):
            if turn.get("speaker") == "customer":
                raw_intent = turn.get("expected_intent") or "out_of_scope"
                canonical_intent = taxonomy.resolve_alias(raw_intent)
                customer_history.append(turn["text"])

                # Provide multi-turn joined text matching runtime (last <= 3 turns)
                multi_turn_text = " [TURN] ".join(customer_history[-3:])
                scenario_records.append(
                    {
                        "text": multi_turn_text,
                        "standalone_text": turn["text"],
                        "intent": canonical_intent,
                        "scenario_id": scenario_id,
                        "turn_id": turn.get("turn_id"),
                        "is_scenario": True,
                    }
                )
    return scenario_records


def build_splits(
    banking_train_path: Path,
    banking_test_path: Path,
    scenarios_dir: Path,
    output_dir: Path,
    val_ratio: float = 0.10,
    seed: int = 42,
) -> dict[str, int]:
    """Build and write versioned JSONL splits."""
    random.seed(seed)
    taxonomy = TaxonomyRegistry()

    # 1. Load data
    train_records = load_banking77(banking_train_path)
    test_records = load_banking77(banking_test_path)
    scenario_records = load_golden_scenarios(scenarios_dir, taxonomy)

    # 2. Stratified train/val split
    by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in train_records:
        canonical = taxonomy.resolve_alias(r["category"])
        by_category[canonical].append({"text": r["text"], "intent": canonical})

    train_split: list[dict[str, Any]] = []
    val_split: list[dict[str, Any]] = []

    for _cat, items in by_category.items():
        random.shuffle(items)
        val_count = max(1, int(len(items) * val_ratio))
        val_split.extend(items[:val_count])
        train_split.extend(items[val_count:])

    # 3. Add out-of-scope data
    shuffled_oos = list(OOS_UTTERANCES)
    random.shuffle(shuffled_oos)

    oos_val_count = max(5, int(len(shuffled_oos) * 0.20))
    oos_test_count = max(5, int(len(shuffled_oos) * 0.20))

    oos_val = shuffled_oos[:oos_val_count]
    oos_test = shuffled_oos[oos_val_count : oos_val_count + oos_test_count]
    oos_train = shuffled_oos[oos_val_count + oos_test_count :]

    for text in oos_train:
        train_split.append({"text": text, "intent": "out_of_scope", "synthetic": True})
    for text in oos_val:
        val_split.append({"text": text, "intent": "out_of_scope", "synthetic": True})

    # Add scenario customer records to training split
    for s in scenario_records:
        train_split.append(
            {
                "text": s["text"],
                "intent": s["intent"],
                "is_scenario": True,
            }
        )
        if s.get("standalone_text") and s["standalone_text"] != s["text"]:
            train_split.append(
                {
                    "text": s["standalone_text"],
                    "intent": s["intent"],
                    "is_scenario": True,
                }
            )

    # 4. Build canonical test split
    canonical_test: list[dict[str, Any]] = []
    for r in test_records:
        canonical = taxonomy.resolve_alias(r["category"])
        canonical_test.append({"text": r["text"], "intent": canonical})

    for text in oos_test:
        canonical_test.append({"text": text, "intent": "out_of_scope", "synthetic": True})

    # Guarantee strict split isolation: remove test utterances from train/val
    test_texts = {r["text"].strip().lower() for r in canonical_test}
    train_split = [r for r in train_split if r["text"].strip().lower() not in test_texts]
    val_split = [r for r in val_split if r["text"].strip().lower() not in test_texts]

    # Shuffle splits
    random.shuffle(train_split)
    random.shuffle(val_split)
    random.shuffle(canonical_test)

    # 5. Build Label Mapping covering all taxonomy definitions (taxonomy version tx-14)
    all_taxonomy_labels = {defn.label for defn in taxonomy.list_all_intents()}
    all_data_labels = {
        item["intent"] for item in train_split + val_split + canonical_test + scenario_records
    }
    all_labels = sorted(all_taxonomy_labels | all_data_labels)
    label2id = {lbl: i for i, lbl in enumerate(all_labels)}
    id2label = {i: lbl for lbl, i in label2id.items()}

    output_dir.mkdir(parents=True, exist_ok=True)

    # Write files
    def write_jsonl(path: Path, data: list[dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

    write_jsonl(output_dir / "train.jsonl", train_split)
    write_jsonl(output_dir / "val.jsonl", val_split)
    write_jsonl(output_dir / "test.jsonl", canonical_test)
    write_jsonl(output_dir / "golden_scenarios.jsonl", scenario_records)

    # Write label map
    label_map = {
        "version": taxonomy.version,
        "num_classes": len(all_labels),
        "label2id": label2id,
        "id2label": id2label,
        "classes": all_labels,
    }
    with open(output_dir / "label_map.json", "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2)

    return {
        "train": len(train_split),
        "val": len(val_split),
        "test": len(canonical_test),
        "scenarios": len(scenario_records),
        "num_classes": len(all_labels),
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    b_train = repo_root / "data" / "raw" / "banking77" / "train.csv"
    b_test = repo_root / "data" / "raw" / "banking77" / "test.csv"
    scenarios_dir = repo_root / "eval" / "scenarios"
    out_dir = repo_root / "data" / "processed" / "intent"

    stats = build_splits(b_train, b_test, scenarios_dir, out_dir)
    print(f"Dataset preparation complete: {stats}")


if __name__ == "__main__":
    main()
