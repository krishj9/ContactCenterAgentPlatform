"""FAQ normalizer."""

from app.pipeline.normalizers.base import BaseNormalizer
from app.pipeline.schemas.normalized_record import (
    NormalizedMetadata,
    NormalizedRecord,
    SourceType,
    StoreType,
)
from app.pipeline.schemas.raw_record_types import FAQRawRow
from app.pipeline.utils.hashing import sha256_text
from app.pipeline.utils.ids import build_id
from app.pipeline.utils.text_cleaning import clean_text, clip_text


class FAQNormalizer(BaseNormalizer[FAQRawRow]):
    """Normalize FAQ pairs to FAQ store records."""

    def normalize(self, raw_row: FAQRawRow) -> NormalizedRecord | None:
        question = clean_text(raw_row.get("question"))
        answer = clean_text(raw_row.get("answer"))
        category = clean_text(raw_row.get("category"))

        if not question or not answer:
            return None

        text = f"Question: {question}\nAnswer: {answer}"
        record_id = build_id("bankfaqs", category or "general", raw_row.get("row_id", ""))

        return NormalizedRecord(
            id=record_id,
            source=SourceType.BANKFAQS,
            store_type=StoreType.FAQ,
            title=question,
            text=text,
            text_for_embedding=text,
            metadata=NormalizedMetadata(
                dataset=SourceType.BANKFAQS,
                store_type=StoreType.FAQ,
                source_row_id=raw_row.get("row_id"),
                category=category or "general",
                question=question,
                answer_preview=clip_text(answer, 180),
                use_case="faq_kb",
                tags=["faq", "banking"],
            ),
            content_hash=sha256_text(text),
        )
