"""Unit tests verifying serialization parity between Python Pydantic contracts and TypeScript interfaces."""

import re
from pathlib import Path
from typing import get_args

from app.contracts.events_v1 import (
    WebSocketEvent,
)

TS_CONTRACTS_PATH = Path("apps/web/src/types/contracts.ts")


def test_typescript_file_exists():
    assert TS_CONTRACTS_PATH.exists(), f"TypeScript contract file missing at {TS_CONTRACTS_PATH}"


def test_all_event_types_present_in_typescript():
    """Verify that every event type in the Pydantic discriminated union is present in TypeScript."""
    ts_content = TS_CONTRACTS_PATH.read_text(encoding="utf-8")

    # Extract all Pydantic event types from the discriminated union
    # In Pydantic, get_args on Annotated returns (UnionType, FieldInfo)
    union_type = get_args(WebSocketEvent)[0]
    python_event_classes = get_args(union_type)

    for cls in python_event_classes:
        event_type_str = cls.model_fields["type"].default
        # Assert type: 'event.type' is defined in TypeScript
        expected_pattern = rf"type:\s*['\"]{re.escape(event_type_str)}['\"]"
        assert re.search(expected_pattern, ts_content), (
            f"Event type '{event_type_str}' from {cls.__name__} not found in {TS_CONTRACTS_PATH}"
        )


def test_provenance_fields_present_in_typescript():
    """Verify provenance metadata fields are strictly declared in TypeScript."""
    ts_content = TS_CONTRACTS_PATH.read_text(encoding="utf-8")

    required_provenance_fields = [
        "model_version: string",
        "taxonomy_version: string",
        "corpus_version: string",
        "prompt_version: string",
    ]
    for field in required_provenance_fields:
        assert field in ts_content, f"Provenance field '{field}' missing from TypeScript contract"
