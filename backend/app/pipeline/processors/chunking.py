"""Heading-aware Markdown chunker (P3.4).

Chunks structured Markdown policy documents (300-500 tokens, 15% overlap)
preserving numbered operational procedures contiguously without splitting steps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.pipeline.schemas.normalized_record import NormalizedRecord


def estimate_tokens(text: str) -> int:
    """Fast, deterministic token count estimation (approx 1.3 tokens per whitespace word)."""
    words = len(text.strip().split())
    return max(1, int(words * 1.3))


@dataclass
class PolicyChunk:
    """Individual chunk output ready for embedding and vector indexing."""

    chunk_id: str
    store_type: str
    policy_id: str
    title: str
    section_heading: str
    text: str
    token_count: int
    intent_labels: list[str]
    risk_level: str
    status: str
    version_tag: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "store_type": self.store_type,
            "policy_id": self.policy_id,
            "title": self.title,
            "section_heading": self.section_heading,
            "text": self.text,
            "token_count": self.token_count,
            "intent_labels": self.intent_labels,
            "risk_level": self.risk_level,
            "status": self.status,
            "version_tag": self.version_tag,
            "metadata": self.metadata,
        }


class HeadingAwareMarkdownChunker:
    """Heading-aware chunker for Markdown policy documents."""

    def __init__(
        self,
        target_min_tokens: int = 300,
        target_max_tokens: int = 500,
        overlap_ratio: float = 0.15,
    ) -> None:
        self.target_min_tokens = target_min_tokens
        self.target_max_tokens = target_max_tokens
        self.overlap_ratio = overlap_ratio

    def chunk_record(self, record: NormalizedRecord) -> list[PolicyChunk]:
        """Split a normalized policy record into heading-aware chunks."""
        extra = record.metadata.extra
        policy_id = str(extra.get("policy_id", record.id))
        doc_title = record.title or "Policy Document"
        version_tag = record.version or "v1.0"
        status = str(extra.get("status", "active"))
        risk_level = str(extra.get("risk_level", "medium"))
        intent_labels = list(extra.get("intent_labels", []))
        if not intent_labels and record.metadata.intent_label:
            intent_labels = [record.metadata.intent_label]

        sections = self._parse_sections(record.text)
        chunks: list[PolicyChunk] = []

        chunk_counter = 1
        for sec_idx, (heading, blocks) in enumerate(sections, start=1):
            sec_chunks = self._chunk_section_blocks(
                doc_title=doc_title,
                heading=heading,
                blocks=blocks,
            )

            for chunk_idx, (chunk_title, chunk_body) in enumerate(sec_chunks, start=1):
                clean_pid = policy_id.lower().replace("-", "_")
                chunk_id = f"{clean_pid}_s{sec_idx}_c{chunk_idx}"
                tok_count = estimate_tokens(chunk_body)

                meta = {
                    "policy_id": policy_id,
                    "doc_title": doc_title,
                    "section_heading": heading,
                    "intent_labels": intent_labels,
                    "risk_level": risk_level,
                    "status": status,
                    "version_tag": version_tag,
                    "owner": extra.get("owner", ""),
                    "effective_from": extra.get("effective_from"),
                    "effective_to": extra.get("effective_to"),
                    "token_count": tok_count,
                }

                chunks.append(
                    PolicyChunk(
                        chunk_id=chunk_id,
                        store_type="policy",
                        policy_id=policy_id,
                        title=chunk_title,
                        section_heading=heading,
                        text=chunk_body,
                        token_count=tok_count,
                        intent_labels=intent_labels,
                        risk_level=risk_level,
                        status=status,
                        version_tag=version_tag,
                        metadata=meta,
                    )
                )
                chunk_counter += 1

        return chunks

    def _parse_sections(self, markdown_text: str) -> list[tuple[str, list[str]]]:
        """Split Markdown into sections by heading (#, ##, ###) while preserving block structure."""
        heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(markdown_text))

        if not matches:
            # No headings, treat entire text as single section
            blocks = self._split_into_blocks(markdown_text)
            return [("General Overview", blocks)]

        sections: list[tuple[str, list[str]]] = []
        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
            sec_body = markdown_text[start_pos:end_pos].strip()
            blocks = self._split_into_blocks(sec_body)
            if blocks:
                sections.append((heading, blocks))

        return sections

    def _split_into_blocks(self, text: str) -> list[str]:
        """Split section body into semantic blocks, keeping numbered steps atomic."""
        raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        blocks: list[str] = []

        for para in raw_paragraphs:
            # Check if paragraph is a numbered procedure list (e.g. 1. Step 1: ... \n 2. Step 2: ...)
            numbered_lines = re.findall(r"(?:^|\n)(\d+\.\s+[^\n]+)", para)
            if len(numbered_lines) >= 2:
                # Keep whole procedure sequence contiguous if reasonable, or item by item
                # Group related numbered steps
                blocks.append(para)
            else:
                blocks.append(para)

        return blocks

    def _chunk_section_blocks(
        self,
        doc_title: str,
        heading: str,
        blocks: list[str],
    ) -> list[tuple[str, str]]:
        """Combine section blocks into target token chunks with overlap."""
        if not blocks:
            return []

        section_prefix = f"Policy: {doc_title}\nSection: {heading}\n\n"
        prefix_tokens = estimate_tokens(section_prefix)
        effective_max = max(150, self.target_max_tokens - prefix_tokens)

        # Calculate block tokens
        block_tokens = [estimate_tokens(b) for b in blocks]
        total_tokens = sum(block_tokens)

        # If entire section fits within target_max_tokens, keep as single chunk
        if total_tokens <= effective_max:
            body = "\n\n".join(blocks)
            full_chunk_text = f"{section_prefix}{body}"
            chunk_title = f"{doc_title} — {heading}"
            return [(chunk_title, full_chunk_text)]

        # Otherwise, split across blocks with ~15% overlap
        chunks: list[tuple[str, str]] = []
        current_blocks: list[str] = []
        current_tokens = 0
        overlap_tokens_target = int(self.target_max_tokens * self.overlap_ratio)

        for block, b_tokens in zip(blocks, block_tokens, strict=False):
            if current_blocks and (current_tokens + b_tokens > effective_max):
                # Emit current chunk
                body = "\n\n".join(current_blocks)
                full_chunk_text = f"{section_prefix}{body}"
                chunk_title = f"{doc_title} — {heading} (Part {len(chunks) + 1})"
                chunks.append((chunk_title, full_chunk_text))

                # Compute overlap from end of current_blocks
                overlap_blocks: list[str] = []
                overlap_accum = 0
                for prev_b in reversed(current_blocks):
                    prev_tok = estimate_tokens(prev_b)
                    if overlap_accum + prev_tok <= overlap_tokens_target:
                        overlap_blocks.insert(0, prev_b)
                        overlap_accum += prev_tok
                    else:
                        break

                current_blocks = list(overlap_blocks)
                current_tokens = sum(estimate_tokens(b) for b in current_blocks)

            current_blocks.append(block)
            current_tokens += b_tokens

        if current_blocks:
            body = "\n\n".join(current_blocks)
            full_chunk_text = f"{section_prefix}{body}"
            part_str = f" (Part {len(chunks) + 1})" if chunks else ""
            chunk_title = f"{doc_title} — {heading}{part_str}"
            chunks.append((chunk_title, full_chunk_text))

        return chunks
