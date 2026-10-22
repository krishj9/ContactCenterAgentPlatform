"""Loader for FAQ CSV files."""

import csv
from collections.abc import Iterator
from pathlib import Path

from app.pipeline.schemas.raw_record_types import FAQRawRow


def load_faq_csv(path: str | Path) -> Iterator[FAQRawRow]:
    """Load FAQ CSV and yield raw rows."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"FAQ file not found: {path}")

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            yield {
                "question": row.get("Question") or row.get("question") or "",
                "answer": row.get("Answer") or row.get("answer") or "",
                "category": row.get("Category") or row.get("category") or "",
                "row_id": str(idx),
            }
