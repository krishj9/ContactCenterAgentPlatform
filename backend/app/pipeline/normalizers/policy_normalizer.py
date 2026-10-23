"""Policy document normalizer (P3.4).

Normalizes raw Markdown policies with frontmatter into canonical NormalizedRecord objects.
"""

from __future__ import annotations

from app.pipeline.normalizers.base import BaseNormalizer
from app.pipeline.schemas.normalized_record import (
    NormalizedMetadata,
    NormalizedRecord,
    SourceType,
    StoreType,
)
from app.pipeline.schemas.raw_record_types import PolicyRawRecord
from app.pipeline.utils.hashing import sha256_text
from app.pipeline.utils.text_cleaning import clean_text, clip_text


class PolicyNormalizer(BaseNormalizer[PolicyRawRecord]):
    """Normalize authored Markdown policy records to canonical policy store format."""

    def normalize(self, raw_row: PolicyRawRecord) -> NormalizedRecord | None:
        policy_id = raw_row.get("policy_id", "").strip()
        title = clean_text(raw_row.get("title", ""))
        content = raw_row.get("content", "").strip()
        version = raw_row.get("version", "v1.0")
        intent_labels = raw_row.get("intent_labels", [])
        risk_level = raw_row.get("risk_level", "medium")
        status = raw_row.get("status", "active")
        owner = raw_row.get("owner", "Compliance")

        if not policy_id or not title or not content:
            return None

        # Standardize record ID
        record_id = f"policy_{policy_id.lower().replace('-', '_')}"
        primary_intent = intent_labels[0] if intent_labels else None

        text_for_embedding = f"Policy: {title}\nID: {policy_id}\n\n{content}"

        return NormalizedRecord(
            id=record_id,
            source=SourceType.POLICY,
            store_type=StoreType.POLICY,
            title=title,
            text=content,
            text_for_embedding=text_for_embedding,
            metadata=NormalizedMetadata(
                dataset=SourceType.POLICY,
                store_type=StoreType.POLICY,
                source_row_id=policy_id,
                category="policy",
                intent_label=primary_intent,
                question=title,
                answer_preview=clip_text(content, 200),
                tags=["policy", risk_level, status, *intent_labels],
                use_case="policy_store",
                extra={
                    "policy_id": policy_id,
                    "version": version,
                    "intent_labels": intent_labels,
                    "risk_level": risk_level,
                    "owner": owner,
                    "effective_from": raw_row.get("effective_from"),
                    "effective_to": raw_row.get("effective_to"),
                    "status": status,
                    "file_path": raw_row.get("file_path", ""),
                },
            ),
            content_hash=sha256_text(text_for_embedding),
            version=version,
        )
