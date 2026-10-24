# ADR-001: Classifier-Based Intent Detection vs. Pure RAG

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board
* **Context**: Technical Specification §2.1, Requirements R8/R9

---

## Context & Problem Statement
In real-time contact center dialogues, the agent UI requires sub-second updates regarding detected customer issues to minimize dead air and establish early situational awareness. An initial architectural proposal considered passing the entire dialogue transcript directly to a Large Language Model (e.g., Gemini 1.5 Flash) via Retrieval-Augmented Generation (RAG) to infer intent and generate recommendations in a single round-trip.

However, full LLM generation exhibits a p95 latency of 1,200ms to 2,200ms. Waiting for full LLM generation before showing the agent the detected intent causes perceptible lag and prevents early retrieval filtering.

## Decision
We decided to decouple intent detection from next-best action generation using a **two-stage hybrid architecture**:
1. **Stage 1 (Fast Path)**: A fine-tuned **Gemma 3 1B LoRA** sequence classifier deployed on Vertex AI endpoints (ONNX Runtime int8 locally). It classifies intent across 77 canonical banking categories in **< 60ms (p95)**, immediately emitting `issue.update` events.
2. **Stage 2 (Assist Path)**: The predicted intent label and confidence score are passed to the PostgreSQL pgvector hybrid search engine and the Gemini Flash generator to produce grounded recommendations and response drafts concurrently.

## Consequences

### Positive
* **Deterministic Latency**: Intent is surfaced to the agent UI in < 60ms from turn completion.
* **Calibrated Confidence**: The linear classifier head provides calibrated probabilities for guardrail enforcement (`INTENT_CONFIDENCE_THRESHOLD = 0.70`).
* **Cost Efficiency**: High-frequency conversational turns avoid expensive LLM token consumption on non-actionable or out-of-scope utterances.

### Negative / Trade-offs
* Requires dedicated ML training and canary promotion pipelines (`ml/pipelines/intent_train.py`, `promote_intent.py`).
* Model vocabulary and intent drift must be tracked via entropy monitoring (`ml/monitoring/intent_monitor.py`).
