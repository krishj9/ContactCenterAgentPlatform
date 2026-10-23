"""Retrieval Evaluation Harness (P3.12).

Measures Recall@k (k=1, 5, 10, 20) and nDCG@5 across evaluation qrels.
Enforces the Phase P3 exit criterion: Recall@20 >= 0.95.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from pathlib import Path
from typing import Any

from app.adapters.local.embedder import LocalEmbedder
from pipeline.loaders.policy_loader import load_policy_markdown_files
from pipeline.normalizers.policy_normalizer import PolicyNormalizer
from pipeline.processors.chunking import HeadingAwareMarkdownChunker

repo_root = Path(__file__).resolve().parent.parent.parent


def compute_ndcg_at_k(retrieved_ids: list[str], ground_truth_ids: set[str], k: int = 5) -> float:
    """Compute Normalized Discounted Cumulative Gain at rank k."""
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k], start=1):
        rel = 1.0 if doc_id in ground_truth_ids else 0.0
        dcg += (math.pow(2.0, rel) - 1.0) / math.log2(i + 1.0)

    # Ideal DCG
    ideal_hits = min(len(ground_truth_ids), k)
    idcg = sum((math.pow(2.0, 1.0) - 1.0) / math.log2(i + 1.0) for i in range(1, ideal_hits + 1))

    if idcg == 0.0:
        return 1.0
    return dcg / idcg


class InMemoryHybridIndex:
    """Offline reference index for standalone retrieval evaluation."""

    def __init__(self, embedder: LocalEmbedder) -> None:
        self.embedder = embedder
        self.chunks: list[dict[str, Any]] = []
        self.vectors: list[list[float]] = []

    async def build(self, policy_dir: Path) -> None:
        normalizer = PolicyNormalizer()
        chunker = HeadingAwareMarkdownChunker()
        records = list(load_policy_markdown_files(policy_dir))

        all_chunks = []
        for raw in records:
            norm = normalizer.normalize(raw)
            if norm:
                chunks = chunker.chunk_record(norm)
                all_chunks.extend(chunks)

        self.chunks = [c.to_dict() for c in all_chunks]
        texts = [c["text"] for c in self.chunks]
        self.vectors = await self.embedder.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        return dot

    async def search(
        self,
        query: str,
        query_vec: list[float],
        top_k: int = 20,
        intent_filter: str | None = None,
    ) -> list[tuple[str, float]]:
        """Dense + lexical hybrid search with RRF."""
        # 1. Dense ranking
        dense_scores = []
        for _idx, (chunk, vec) in enumerate(zip(self.chunks, self.vectors, strict=False)):
            if intent_filter and intent_filter not in chunk.get("intent_labels", []):
                # Filter relax: apply penalty if intent doesn't match
                penalty = 0.5
            else:
                penalty = 1.0
            sim = self._cosine(query_vec, vec) * penalty
            dense_scores.append((chunk["chunk_id"], sim))

        dense_scores.sort(key=lambda x: x[1], reverse=True)
        dense_ranks = {cid: rank for rank, (cid, _) in enumerate(dense_scores, start=1)}

        # 2. Lexical term match ranking
        q_tokens = set(query.lower().split())
        lex_scores = []
        for chunk in self.chunks:
            c_tokens = set(chunk["text"].lower().split())
            overlap = len(q_tokens.intersection(c_tokens))
            lex_scores.append((chunk["chunk_id"], overlap))

        lex_scores.sort(key=lambda x: x[1], reverse=True)
        sparse_ranks = {cid: rank for rank, (cid, _) in enumerate(lex_scores, start=1)}

        # 3. RRF (k=60, w_dense=0.6, w_sparse=0.4)
        rrf: dict[str, float] = {}
        for chunk in self.chunks:
            cid = chunk["chunk_id"]
            d_rank = dense_ranks.get(cid, 999)
            s_rank = sparse_ranks.get(cid, 999)
            score = (0.6 / (60 + d_rank)) + (0.4 / (60 + s_rank))
            rrf[cid] = score

        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


async def evaluate_retrieval(
    qrels_path: Path | None = None,
    policy_dir: Path | None = None,
) -> dict[str, float]:
    """Run evaluation and compute retrieval metrics."""
    qrels_path = qrels_path or repo_root / "eval" / "retrieval" / "qrels.jsonl"
    policy_dir = policy_dir or repo_root / "corpora" / "policy"

    embedder = LocalEmbedder()
    index = InMemoryHybridIndex(embedder)
    await index.build(policy_dir)

    queries: list[dict[str, Any]] = []
    with open(qrels_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))

    recall_at_1 = 0
    recall_at_5 = 0
    recall_at_10 = 0
    recall_at_20 = 0
    ndcg_at_5_total = 0.0

    print(f"\n--- Running Retrieval Evaluation on {len(queries)} queries ---")

    for q in queries:
        query_text = q["query"]
        expected_ids = set(q.get("expected_chunk_ids", []))
        intent = q.get("intent")

        q_vec = await embedder.embed_query(query_text)
        results = await index.search(
            query=query_text, query_vec=q_vec, top_k=20, intent_filter=intent
        )
        retrieved_ids = [r[0] for r in results]

        # Calculate Recall@k
        if any(cid in retrieved_ids[:1] for cid in expected_ids):
            recall_at_1 += 1
        if any(cid in retrieved_ids[:5] for cid in expected_ids):
            recall_at_5 += 1
        if any(cid in retrieved_ids[:10] for cid in expected_ids):
            recall_at_10 += 1
        if any(cid in retrieved_ids[:20] for cid in expected_ids):
            recall_at_20 += 1

        ndcg = compute_ndcg_at_k(retrieved_ids, expected_ids, k=5)
        ndcg_at_5_total += ndcg

    total = len(queries)
    metrics = {
        "Recall@1": recall_at_1 / total,
        "Recall@5": recall_at_5 / total,
        "Recall@10": recall_at_10 / total,
        "Recall@20": recall_at_20 / total,
        "nDCG@5": ndcg_at_5_total / total,
    }

    print("\n================ Retrieval Evaluation Results ================")
    for k, v in metrics.items():
        print(f"  {k:12s}: {v:.4f} ({v * 100:.1f}%)")
    print("==============================================================")

    # Assert Exit Criteria
    if metrics["Recall@20"] < 0.95:
        raise AssertionError(
            f"❌ Recall@20 ({metrics['Recall@20']:.4f}) failed to meet exit criteria of >= 0.95!"
        )

    print("✅ Exit criteria PASSED: Recall@20 >= 0.95!")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieval Evaluation Harness")
    parser.add_argument("--qrels", default=None, help="Path to qrels.jsonl")
    args = parser.parse_args()

    qrels_path = Path(args.qrels) if args.qrels else None
    asyncio.run(evaluate_retrieval(qrels_path=qrels_path))


if __name__ == "__main__":
    main()
