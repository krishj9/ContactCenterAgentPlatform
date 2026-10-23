"""Conversational Multi-Turn Augmentation for Intent Classifier (P4.2).

Generates realistic spoken conversational dialogue noise including ASR disfluencies,
casing variations, missing punctuation, and multi-turn joins with [TURN] delimiters.
Outputs ml/intent/data/spotcheck.md for manual quality audit.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

DISFLUENCIES = [
    "uh",
    "um",
    "like",
    "you know",
    "i mean",
    "well",
    "so basically",
    "actually",
    "wait",
]

PREV_TURNS_CONTEXT = [
    "hello thanks for taking my call",
    "yes i was hoping you could help me with something",
    "hi i am calling about my account",
    "good afternoon i have a quick question",
    "hey there i have an issue on my mobile app",
    "yes my name is on the account",
    "thanks for waiting i just logged in",
]


def strip_punctuation(text: str) -> str:
    """Remove trailing and internal punctuation, common in streaming STT models."""
    return re.sub(r"[^\w\s]", "", text)


def inject_disfluency(text: str, rng: random.Random) -> str:
    """Insert spoken disfluencies into an utterance."""
    words = text.split()
    if not words:
        return text

    mode = rng.choice(["prefix", "infix", "repeat", "clean"])

    if mode == "prefix":
        filler = rng.choice(DISFLUENCIES)
        return f"{filler} {text}"
    elif mode == "infix" and len(words) > 3:
        idx = rng.randint(1, len(words) - 2)
        filler = rng.choice(DISFLUENCIES)
        words.insert(idx, filler)
        return " ".join(words)
    elif mode == "repeat":
        first = words[0]
        return f"{first} {first} {' '.join(words[1:])}"
    return text


def create_multi_turn_utterance(
    current_turn: str,
    rng: random.Random,
    prob_multiturn: float = 0.40,
) -> str:
    """Join up to 3 turns using the [TURN] delimiter."""
    if rng.random() > prob_multiturn:
        return current_turn

    num_prev_turns = rng.choice([1, 2])
    prev_turns = rng.sample(PREV_TURNS_CONTEXT, num_prev_turns)
    all_turns = prev_turns + [current_turn]
    return " [TURN] ".join(all_turns)


def augment_record(record: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """Apply conversational augmentation pipeline to a single record."""
    raw_text = record["text"]

    # 1. Spoken disfluency
    noisy_text = inject_disfluency(raw_text, rng)

    # 2. Punctuation stripping / lowercase formatting
    if rng.random() < 0.70:
        noisy_text = strip_punctuation(noisy_text).lower()

    # 3. Multi-turn [TURN] join
    formatted_text = create_multi_turn_utterance(noisy_text, rng)

    return {
        "text": formatted_text,
        "intent": record["intent"],
        "original_text": raw_text,
        "synthetic": True,
        "is_augmented": True,
    }


def augment_dataset(
    input_jsonl: Path,
    output_jsonl: Path,
    spotcheck_md: Path,
    sample_ratio: float = 0.35,
    seed: int = 42,
) -> dict[str, int]:
    """Augment a fraction of the training dataset and emit spotcheck report."""
    rng = random.Random(seed)

    records: list[dict[str, Any]] = []
    with open(input_jsonl, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    augmented_records: list[dict[str, Any]] = list(records)
    spotcheck_samples: list[tuple[str, str, str]] = []

    # Augment a stratified sample of records
    to_augment = [r for r in records if not r.get("synthetic", False)]
    sampled = rng.sample(to_augment, int(len(to_augment) * sample_ratio))

    for item in sampled:
        aug = augment_record(item, rng)
        augmented_records.append(aug)
        if len(spotcheck_samples) < 15:
            spotcheck_samples.append((item["text"], aug["text"], item["intent"]))

    rng.shuffle(augmented_records)

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in augmented_records:
            f.write(json.dumps(r) + "\n")

    # Generate spotcheck.md
    spotcheck_md.parent.mkdir(parents=True, exist_ok=True)
    with open(spotcheck_md, "w", encoding="utf-8") as f:
        f.write("# Conversational Augmentation Spotcheck Review (P4.2)\n\n")
        f.write("Human review spotcheck of synthetic ASR-style noise and multi-turn joins.\n\n")
        f.write("| Intent | Original Utterance | Augmented Spoken Turns (with [TURN]) |\n")
        f.write("|---|---|---|\n")
        for orig, aug_text, intent in spotcheck_samples:
            clean_orig = orig.replace("|", "\\|")
            clean_aug = aug_text.replace("|", "\\|")
            f.write(f"| `{intent}` | {clean_orig} | {clean_aug} |\n")

    return {
        "original_records": len(records),
        "augmented_records": len(augmented_records),
        "added_samples": len(augmented_records) - len(records),
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    train_in = repo_root / "data" / "processed" / "intent" / "train.jsonl"
    train_out = repo_root / "data" / "processed" / "intent" / "train_augmented.jsonl"
    spotcheck = repo_root / "ml" / "intent" / "data" / "spotcheck.md"

    res = augment_dataset(train_in, train_out, spotcheck)
    print(f"Augmentation complete: {res}")


if __name__ == "__main__":
    main()
