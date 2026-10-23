"""Unit tests for retrieval evaluation harness and metrics (P3.12)."""

from __future__ import annotations

import pytest

from eval.retrieval.run import compute_ndcg_at_k, evaluate_retrieval


def test_ndcg_calculation() -> None:
    ground_truth = {"c1", "c2"}

    # Perfect ranking: both ground truth at top positions
    perfect = ["c1", "c2", "c3", "c4", "c5"]
    assert pytest.approx(compute_ndcg_at_k(perfect, ground_truth, k=5), 0.001) == 1.0

    # Miss all ground truth
    zero = ["c3", "c4", "c5", "c6", "c7"]
    assert compute_ndcg_at_k(zero, ground_truth, k=5) == 0.0

    # Intermediate ranking: 1 hit at rank 1, 1 hit at rank 4
    mixed = ["c1", "c3", "c4", "c2", "c5"]
    score = compute_ndcg_at_k(mixed, ground_truth, k=5)
    assert 0.5 < score < 1.0


@pytest.mark.asyncio
async def test_retrieval_eval_meets_exit_criteria() -> None:
    # Runs the evaluation on the authored qrels and asserts Recall@20 >= 0.95
    metrics = await evaluate_retrieval()
    assert metrics["Recall@20"] >= 0.95
    assert metrics["Recall@5"] >= 0.90
    assert metrics["nDCG@5"] >= 0.70
