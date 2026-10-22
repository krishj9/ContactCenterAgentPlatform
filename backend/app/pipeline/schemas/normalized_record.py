"""Canonical normalized schema for all datasets."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class StoreType(StrEnum):
    INTENT = "intent"
    FAQ = "faq"
    POLICY = "policy"
    COMPLAINT_EVAL = "complaint_eval"


class SourceType(StrEnum):
    BANKING77 = "banking77"
    BANKFAQS = "bankfaqs"
    CFPB = "cfpb"
    POLICY = "policy"


class NormalizedMetadata(BaseModel):
    dataset: SourceType
    store_type: StoreType
    source_row_id: str | None = None
    split: str | None = None
    category: str | None = None
    intent_label: str | None = None
    product: str | None = None
    issue: str | None = None
    sub_issue: str | None = None
    question: str | None = None
    answer_preview: str | None = None
    date_received: date | None = None
    tags: list[str] = Field(default_factory=list)
    language: str = "en"
    use_case: str
    quality_score: float | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class NormalizedRecord(BaseModel):
    id: str
    source: SourceType
    store_type: StoreType
    title: str | None = None
    text: str
    text_for_embedding: str
    metadata: NormalizedMetadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_hash: str
    version: str = "v1"

    @field_validator("text", "text_for_embedding", mode="before")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("text fields must not be empty")
        return value
