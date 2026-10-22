"""Banking77 normalizer."""

from app.pipeline.normalizers.base import BaseNormalizer
from app.pipeline.schemas.normalized_record import (
    NormalizedMetadata,
    NormalizedRecord,
    SourceType,
    StoreType,
)
from app.pipeline.schemas.raw_record_types import Banking77RawRow
from app.pipeline.utils.hashing import sha256_text
from app.pipeline.utils.ids import build_id
from app.pipeline.utils.text_cleaning import clean_text


class Banking77Normalizer(BaseNormalizer[Banking77RawRow]):
    """Normalize Banking77 utterance examples to intent store records."""

    def normalize(self, raw_row: Banking77RawRow) -> NormalizedRecord | None:
        text = clean_text(raw_row.get("text"))
        intent_label = clean_text(raw_row.get("label"))
        split = clean_text(raw_row.get("split"))

        if not text or not intent_label:
            return None

        text_for_embedding = f"Intent example: {text}"
        record_id = build_id("banking77", split, intent_label, raw_row.get("row_id", ""))

        return NormalizedRecord(
            id=record_id,
            source=SourceType.BANKING77,
            store_type=StoreType.INTENT,
            title=f"{intent_label} example",
            text=text,
            text_for_embedding=text_for_embedding,
            metadata=NormalizedMetadata(
                dataset=SourceType.BANKING77,
                store_type=StoreType.INTENT,
                source_row_id=raw_row.get("row_id"),
                split=split,
                category=intent_label,
                intent_label=intent_label,
                use_case="intent_example",
                tags=["banking77", "intent"],
            ),
            content_hash=sha256_text(text_for_embedding),
        )
