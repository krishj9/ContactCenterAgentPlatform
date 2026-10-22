"""Tests for FAQ normalizer."""

import pytest

from app.pipeline.normalizers.faq_normalizer import FAQNormalizer
from app.pipeline.schemas.normalized_record import SourceType, StoreType


@pytest.fixture
def normalizer():
    """Create a FAQ normalizer."""
    return FAQNormalizer()


def test_valid_qa_becomes_faq_record(normalizer):
    """Test that a valid question+answer becomes an FAQ store record."""
    raw_row = {
        "question": "How do I transfer money?",
        "answer": "You can transfer money through our mobile app or website.",
        "category": "transfers",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.source == SourceType.BANKFAQS
    assert record.store_type == StoreType.FAQ
    assert record.metadata.question == "How do I transfer money?"
    assert record.metadata.use_case == "faq_kb"
    assert "Question:" in record.text
    assert "Answer:" in record.text


def test_missing_question_returns_none(normalizer):
    """Test that missing question returns None."""
    raw_row = {
        "question": "",
        "answer": "You can transfer money through our mobile app or website.",
        "category": "transfers",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is None


def test_missing_answer_returns_none(normalizer):
    """Test that missing answer returns None."""
    raw_row = {
        "question": "How do I transfer money?",
        "answer": "",
        "category": "transfers",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is None


def test_answer_preview_populated(normalizer):
    """Test that answer_preview is populated and clipped."""
    long_answer = "A" * 200
    raw_row = {
        "question": "How do I transfer money?",
        "answer": long_answer,
        "category": "transfers",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.metadata.answer_preview is not None
    assert len(record.metadata.answer_preview) <= 180
    assert record.metadata.answer_preview.endswith("...")


def test_title_is_question(normalizer):
    """Test that title is set to the question."""
    raw_row = {
        "question": "How do I transfer money?",
        "answer": "You can transfer money through our mobile app or website.",
        "category": "transfers",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.title == "How do I transfer money?"


def test_text_format(normalizer):
    """Test that text is formatted correctly."""
    raw_row = {
        "question": "How do I transfer money?",
        "answer": "Use the app.",
        "category": "transfers",
        "row_id": "0",
    }
    record = normalizer.normalize(raw_row)
    assert record is not None
    assert record.text == "Question: How do I transfer money?\nAnswer: Use the app."
    assert record.text_for_embedding == record.text
