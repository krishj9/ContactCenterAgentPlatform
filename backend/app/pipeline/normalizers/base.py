"""Base normalizer class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TypeVar

from app.pipeline.schemas.normalized_record import NormalizedRecord

T = TypeVar("T")


class BaseNormalizer[T](ABC):
    """Abstract base for dataset-specific normalizers."""

    @abstractmethod
    def normalize(self, raw_row: T) -> NormalizedRecord | None:
        """Normalize a single raw row. Return None to skip."""
        pass

    def normalize_many(self, rows: Iterable[T]) -> list[NormalizedRecord]:
        """Normalize multiple rows, filtering out None results."""
        records: list[NormalizedRecord] = []
        for row in rows:
            record = self.normalize(row)
            if record is not None:
                records.append(record)
        return records
