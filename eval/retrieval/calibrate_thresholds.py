"""RAG Threshold Calibration and Reranker Evaluation (P5.4).

Evaluates cross-encoder reranking over evaluation qrels and calibrates
tau_evidence and tau_policy thresholds for the Grounding State Machine (Spec §3.3.3).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "backend"))

from app.adapters.local.embedder import LocalEmbedder
from app.adapters.local.reranker import LocalReranker
from app.domain.evidence import EvidenceChunk
from app.services.rag.query_builder import RAGQueryBuilder
from eval.retrieval.run import InMemoryHybridIndex, compute_ndcg_at_k

logger = logging.getLogger(__name__)


async def calibrate_and_evaluate(
    qrels_path: Path | None = None,
    policy_dir: Path | None = None,
    output_config_path: Path | None = None,
) -> dict[str, Any]:
    """Run retrieval + reranking over qrels, compute metrics, and write grounding.yaml."""
    qrels_file = qrels_path or repo_root / "eval" / "retrieval" / "qrels.jsonl"
    policy_path = policy_dir or repo_root / "corpora" / "policy"
    out_yaml = output_config_path or repo_root / "config" / "grounding.yaml"

    embedder = LocalEmbedder()
    reranker = LocalReranker()
    index = InMemoryHybridIndex(embedder)
    await index.build(policy_path)

    with open(qrels_file, encoding="utf-8") as f:
        qrels = [json.loads(line) for line in f if line.strip()]

    relevant_scores: list[float] = []
    non_relevant_scores: list[float] = []
    top5_hits = 0
    ndcg_scores: list[float] = []

    query_builder = RAGQueryBuilder()

    for item in qrels:
        raw_query = item["query"]
        expected_ids = set(item.get("expected_chunk_ids", []))

        # 1. Synthesize multi-turn query with intent description (Spec §3.3.2)
        built = query_builder.build_query([raw_query], item.get("intent", ""))
        query_text = built.query_text

        # 2. Retrieve initial candidate pool (top-20)
        query_vec = await embedder.embed_query(query_text)
        hits = await index.search(query_text, query_vec, top_k=20, intent_filter=built.intent_label)
        hit_dict = dict(hits)

        candidates: list[EvidenceChunk] = []
        for c in index.chunks:
            cid = c.get("id") or c.get("chunk_id", "")
            if cid in hit_dict:
                candidates.append(
                    EvidenceChunk(
                        chunk_id=cid,
                        store_type="policy",
                        title=c.get("title", "Policy"),
                        text=c.get("text", ""),
                        similarity_score=hit_dict[cid],
                        intent_labels=c.get("intent_labels", []),
                        risk_level=c.get("risk_level", "medium"),
                    )
                )

        # 2. Cross-encoder rerank
        reranked = await reranker.rerank(query_text, candidates, top_k=5)
        reranked_ids = [c.chunk_id for c in reranked]

        # Metric tracking
        if any(cid in expected_ids for cid in reranked_ids):
            top5_hits += 1

        ndcg = compute_ndcg_at_k(reranked_ids, expected_ids, k=5)
        ndcg_scores.append(ndcg)

        for c in reranked:
            if c.chunk_id in expected_ids:
                relevant_scores.append(c.similarity_score)
            else:
                non_relevant_scores.append(c.similarity_score)

    recall_at_5 = top5_hits / len(qrels) if qrels else 0.0
    mean_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    # Calibrate thresholds (Spec §3.3.3)
    # tau_evidence: minimum score to consider evidence supportive (5th percentile of relevant scores)
    relevant_scores.sort()
    tau_evidence = (
        round(relevant_scores[max(0, int(len(relevant_scores) * 0.05))], 2)
        if relevant_scores
        else 0.65
    )
    # tau_policy: minimum policy procedure confidence
    tau_policy = round(max(0.68, tau_evidence + 0.03), 2)

    config_data = {
        "version": "v1.0",
        "description": "Calibrated Grounding State Machine Thresholds (Spec §3.3.3)",
        "thresholds": {
            "tau_intent": 0.55,
            "tau_evidence": tau_evidence,
            "tau_policy": tau_policy,
            "grounding_similarity_threshold": 0.75,
            "rerank_top_k": 5,
            "retrieval_top_k": 20,
            "verifier_drop_tolerance": 0.30,
        },
        "evaluation_metrics": {
            "policy_recall_at_5": round(recall_at_5, 4),
            "mean_ndcg_at_5": round(mean_ndcg, 4),
            "qrels_count": len(qrels),
        },
    }

    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    print(f"Calibration Complete! Output written to {out_yaml}")
    print(f"Policy Recall@5: {recall_at_5:.4f} (Target >= 0.90)")
    print(f"nDCG@5:          {mean_ndcg:.4f} (Target >= 0.80)")
    print(f"tau_evidence:    {tau_evidence}")
    print(f"tau_policy:      {tau_policy}")

    return config_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calibrate RAG grounding thresholds.")
    parser.add_argument("--qrels", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    asyncio.run(calibrate_and_evaluate(qrels_path=args.qrels, output_config_path=args.output))
