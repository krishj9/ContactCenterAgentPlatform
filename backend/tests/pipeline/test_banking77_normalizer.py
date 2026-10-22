"""Tests for Banking77 normalizer."""

import pytest

from app.pipeline.normalizers.banking77_normalizer import Banking77Normalizer
from app.pipeline.schemas.normalized_record import SourceType, StoreType


@pytest.fixture
def normalizer():
    """Create a Banking77 normalizer."""
    return Banking77Normalizer()


def test_valid_row_becomes_intent_record(normalizer):
    """Test that a valid row becomes an intent store record."""
    raw_row = {
        "text": "I want to transfer money",
        "label": "transfer",
        "category": "transfer",
        "split": "train",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.source == SourceType.BANKING77
    assert record.store_type == StoreType.INTENT
    assert record.metadata.intent_label == "transfer"
    assert record.metadata.use_case == "intent_example"
    assert "Intent example:" in record.text_for_embedding


def test_missing_text_returns_none(normalizer):
    """Test that missing text returns None."""
    raw_row = {
        "text": "",
        "label": "transfer",
        "category": "transfer",
        "split": "train",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is None


def test_missing_label_returns_none(normalizer):
    """Test that missing label returns None."""
    raw_row = {
        "text": "I want to transfer money",
        "label": "",
        "category": "",
        "split": "train",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is None


def test_deterministic_id_shape(normalizer):
    """Test that ID is deterministic and has correct shape."""
    raw_row = {
        "text": "I want to transfer money",
        "label": "transfer",
        "category": "transfer",
        "split": "train",
        "row_id": "42",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert "banking77" in record.id
    assert "train" in record.id
    assert "transfer" in record.id
    assert "42" in record.id


def test_whitespace_normalization(normalizer):
    """Test that whitespace is normalized."""
    raw_row = {
        "text": "  I want to   transfer   money  ",
        "label": "  transfer  ",
        "category": "transfer",
        "split": "train",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.text == "I want to transfer money"
    assert record.metadata.intent_label == "transfer"


def test_title_format(normalizer):
    """Test that title is formatted correctly."""
    raw_row = {
        "text": "I want to transfer money",
        "label": "transfer",
        "category": "transfer",
        "split": "train",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.title == "transfer example"
