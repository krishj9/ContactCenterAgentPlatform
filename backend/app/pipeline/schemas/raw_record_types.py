"""TypedDicts for raw row types from loaders."""

from __future__ import annotations

from typing import TypedDict


class Banking77RawRow(TypedDict, total=False):
    text: str
    label: str
    category: str
    split: str
    row_id: str


class FAQRawRow(TypedDict, total=False):
    question: str
    answer: str
    category: str
    row_id: str


class CFPBRawRow(TypedDict, total=False):
    complaint_id: str
    product: str
    issue: str
    sub_issue: str
    consumer_complaint_narrative: str
    date_received: str
    company: str
    submitted_via: str
    state: str


class PolicyRawRecord(TypedDict, total=False):
    policy_id: str
    version: str
    title: str
    intent_labels: list[str]
    risk_level: str
    owner: str
    effective_from: str
    effective_to: str | None
    status: str
    content: str
    file_path: str
