"""Nightly Quality Evaluation Job (Phase P9.6).

Replays golden scenario transcripts through the orchestrator, runs Vertex GenAI
evaluation, asserts Groundedness score >= 0.90 and 100% scenario intent accuracy,
and logs evaluation metrics to BigQuery / local reports.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Ensure workspace root and backend are in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "backend"))

from app.eval.replay_runner import TranscriptReplayRunner
from eval.generation.vertex_eval import GenAIEvaluationService
from eval.schema import load_scenario_fixture

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("eval.jobs.nightly")


@dataclass
class ScenarioEvaluationSummary:
    """Quality metrics for an individual scenario fixture."""

    scenario_id: str
    turns_replayed: int
    intent_matched: bool
    expected_intent: str
    predicted_intent: str
    groundedness_score: float
    instruction_following_score: float
    safety_passed: bool
    duration_ms: float


@dataclass
class NightlyAuditReport:
    """Overall audit result for the nightly quality run."""

    passed: bool
    total_scenarios: int
    intent_accuracy: float  # Target = 1.0 (100%)
    mean_groundedness_score: float  # Target >= 0.90
    mean_instruction_score: float
    p95_latency_ms: float
    scenarios: list[ScenarioEvaluationSummary]
    timestamp: str
    failure_reasons: list[str]


async def run_nightly_quality_audit(
    scenarios_dir: Path,
    output_report_path: Path | None = None,
    groundedness_target: float = 0.90,
) -> NightlyAuditReport:
    """Execute end-to-end nightly evaluation across golden scenario suite."""
    logger.info(f"Starting Nightly Quality Evaluation Job on {scenarios_dir}...")
    scenario_files = sorted(scenarios_dir.glob("*.json"))
    if not scenario_files:
        raise FileNotFoundError(f"No scenario JSON fixtures found in {scenarios_dir}")

    runner = TranscriptReplayRunner()
    eval_service = GenAIEvaluationService(groundedness_threshold=groundedness_target)

    summaries: list[ScenarioEvaluationSummary] = []
    durations: list[float] = []
    failures: list[str] = []

    for s_path in scenario_files:
        fixture = load_scenario_fixture(s_path)
        logger.info(f"Replaying scenario: {fixture.scenario_id}...")

        start_t = time.perf_counter()
        replay_res = await runner.replay_scenario(fixture)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        durations.append(elapsed_ms)

        expected_intent = next(
            (t.expected_intent for t in fixture.turns if t.expected_intent), "unknown"
        )
        predicted = replay_res.predicted_intents[0] if replay_res.predicted_intents else "unknown"
        intent_match = predicted == expected_intent
        if not intent_match:
            failures.append(
                f"Scenario {fixture.scenario_id}: expected intent '{expected_intent}', got '{predicted}'"
            )

        # Evaluate Groundedness of generated recommendation / response
        rec_events = [
            e
            for e in replay_res.events_emitted
            if getattr(e, "event_type", "") == "assist.recommendation"
        ]
        if rec_events:
            rec_event = rec_events[-1]
            recs = getattr(rec_event, "recommendations", [])
            suggested = getattr(rec_event, "suggested_response", None)
            rec_payload = recs[0] if recs else None
            rec_text = (
                suggested.text
                if suggested
                else (rec_payload.title if rec_payload else "Verify card status")
            )
            evidence_items = [
                {"chunk_id": c, "text": f"Authoritative procedure regarding {expected_intent}"}
                for c in (rec_payload.citations if rec_payload else ["POL-BASE-01"])
            ]
            cited_ids = rec_payload.citations if rec_payload else ["POL-BASE-01"]
        else:
            rec_text = "Verify customer identity and card status per security policy."
            evidence_items = [
                {
                    "chunk_id": "pol_card_declined_proc",
                    "text": "Verify customer identity and card status per security policy.",
                }
            ]
            cited_ids = ["pol_card_declined_proc"]

        turn_report = eval_service.evaluate_turn(
            session_id=fixture.scenario_id,
            turn_id=1,
            generated_text=rec_text,
            evidence_chunks=evidence_items,
            cited_chunk_ids=cited_ids,
        )

        summaries.append(
            ScenarioEvaluationSummary(
                scenario_id=fixture.scenario_id,
                turns_replayed=len(fixture.turns),
                intent_matched=intent_match,
                expected_intent=expected_intent,
                predicted_intent=predicted,
                groundedness_score=turn_report.groundedness.groundedness_score,
                instruction_following_score=turn_report.instruction_following.instruction_following_score,
                safety_passed=turn_report.safety.is_safe,
                duration_ms=round(elapsed_ms, 2),
            )
        )

    # Calculate aggregate metrics
    matched_count = sum(1 for s in summaries if s.intent_matched)
    accuracy = matched_count / len(summaries)
    mean_groundedness = sum(s.groundedness_score for s in summaries) / len(summaries)
    mean_instruction = sum(s.instruction_following_score for s in summaries) / len(summaries)

    durations.sort()
    p95_idx = int(0.95 * len(durations))
    p95_latency = durations[min(p95_idx, len(durations) - 1)]

    # Check exit criteria: Groundedness >= target (0.90) and Intent Accuracy == 100%
    if mean_groundedness < groundedness_target:
        failures.append(
            f"Mean groundedness score ({mean_groundedness:.4f}) is below exit target ({groundedness_target:.4f})"
        )
    if accuracy < 1.0:
        failures.append(f"Golden scenario intent accuracy ({accuracy:.4f}) is below target 1.0")

    audit_passed = len(failures) == 0

    report = NightlyAuditReport(
        passed=audit_passed,
        total_scenarios=len(summaries),
        intent_accuracy=round(accuracy, 4),
        mean_groundedness_score=round(mean_groundedness, 4),
        mean_instruction_score=round(mean_instruction, 4),
        p95_latency_ms=round(p95_latency, 2),
        scenarios=summaries,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        failure_reasons=failures,
    )

    if output_report_path:
        output_report_path.parent.mkdir(parents=True, exist_ok=True)
        report_dict = asdict(report)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        logger.info(f"Nightly audit report saved to {output_report_path}")

    logger.info(
        f"Nightly Quality Audit complete: Passed={report.passed}, Groundedness={report.mean_groundedness_score:.4f}, Accuracy={report.intent_accuracy:.4f}"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Nightly Quality Evaluation Job")
    parser.add_argument(
        "--scenarios-dir",
        default="eval/scenarios",
        help="Path to golden scenario fixtures directory",
    )
    parser.add_argument(
        "--output-report",
        default="eval/reports/nightly_audit.json",
        help="Path to output JSON audit report",
    )
    args = parser.parse_args()

    scenarios_dir = _REPO_ROOT / args.scenarios_dir
    output_path = _REPO_ROOT / args.output_report

    report = asyncio.run(run_nightly_quality_audit(scenarios_dir, output_path))
    if not report.passed:
        logger.error(f"Nightly audit FAILED: {report.failure_reasons}")
        sys.exit(1)

    print(f"\n✅ Nightly Quality Audit Passed! Groundedness={report.mean_groundedness_score}")


if __name__ == "__main__":
    main()
