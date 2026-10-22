"""JSONL writer for normalized records."""

import json
from collections.abc import Iterable
from pathlib import Path

from app.pipeline.schemas.normalized_record import NormalizedRecord


def write_jsonl(path: str | Path, records: Iterable[NormalizedRecord]) -> None:
    """Write records to JSONL file (one JSON object per line)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")
