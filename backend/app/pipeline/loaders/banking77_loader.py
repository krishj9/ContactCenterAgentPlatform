"""Loader for Banking77 CSV files."""

import csv
from collections.abc import Iterator
from pathlib import Path

from app.pipeline.schemas.raw_record_types import Banking77RawRow


def load_banking77_csv(path: str | Path, split: str) -> Iterator[Banking77RawRow]:
    """Load Banking77 CSV and yield raw rows."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Banking77 file not found: {path}")

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            yield {
                "text": row.get("text") or row.get("utterance") or "",
                "label": row.get("label") or row.get("category") or "",
                "category": row.get("category") or row.get("label") or "",
                "split": split,
                "row_id": str(idx),
            }
