# Browser Voice Agent Helper (Banking POC) — Implementation Plan

## 0. Purpose

This document defines the build plan for implementing the application from the ground up using a coding assistant. The plan is dependency-ordered and designed to support local development first, then retrieval-backed real-time assist, then summary, evaluation, and deployment hardening. [file:577]

## 1. Delivery principles

- Build in small, verifiable phases.
- Keep WebSocket handlers thin.
- Keep data contracts explicit.
- Prefer rules-first safety over speculative autonomy.
- Ensure each phase has tests before moving to the next.
- Support local execution early.
- Preserve human-in-the-loop behavior at all times. [file:577]

## 2. Global done criteria

A phase is complete only when:
- Required files are created or updated.
- Acceptance criteria are met.
- Unit and integration tests pass for that phase.
- The feature works in local development mode.
- New contracts are documented where relevant.

## 3. Phase plan

### Phase 0 — Repo bootstrap and developer experience
Goal:
Set up the repository, tooling, local run experience, and basic CI.

Tasks:
- Create backend, frontend, pipeline, data, and docs directories.
- Add Python and Node project scaffolding.
- Add formatter, linter, and test tooling.
- Add `.env.example`.
- Add Docker Compose for local backend/frontend startup if desired.
- Add README with run instructions.
- Add CI workflow for lint and tests.

Deliverables:
- `backend/`
- `frontend/`
- `pipeline/`
- `docs/`
- `.env.example`
- `README.md`
- optional `docker-compose.yml`

Tests:
- Backend test runner executes.
- Frontend test runner executes.
- Lint commands execute successfully.

### Phase 1 — Shared contracts and domain models
Goal:
Define stable models before feature implementation.

Tasks:
- Define session, participant, transcript, issue, recommendation, summary, and audit schemas.
- Define WebSocket event contracts.
- Define configuration settings model.
- Define repository interfaces and service interfaces.

Suggested files:
- `backend/app/models/*.py`
- `backend/app/core/config.py`
- `backend/app/core/events.py`

Acceptance:
- Core models and event schemas are explicit and validated.
- Backend can import all core models without circular dependency issues.

Tests:
- Schema validation tests.
- Event serialization tests.

### Phase 2 — Session lifecycle and WebSocket skeleton
Goal:
Enable session creation, join flow, and socket connectivity.

Tasks:
- Implement session repository with SQLite or in-memory support.
- Implement session API routes.
- Implement join-token generation and validation.
- Implement WebSocket gateway.
- Add session lifecycle events.

Suggested files:
- `backend/app/api/session.py`
- `backend/app/ws/session.py`
- `backend/app/repositories/session_repository.py`
- `backend/tests/api/test_session_api.py`
- `backend/tests/ws/test_session_ws.py`

Acceptance:
- Session can be created and joined by customer and agent.
- Session lifecycle transitions are valid.
- Socket connection works for both roles.

### Phase 3 — Browser UI skeleton
Goal:
Create minimal customer and agent pages.

Tasks:
- Add customer page with join and microphone controls.
- Add agent page with join flow and empty assist panels.
- Add shared WebSocket client utilities.
- Add session state display.

Suggested files:
- `frontend/app/customer/page.tsx`
- `frontend/app/agent/page.tsx`
- `frontend/lib/ws-client.ts`
- `frontend/components/*`

Acceptance:
- Both roles can connect to the backend.
- UI shows session status and connection state.

Tests:
- Basic component rendering tests.
- Minimal end-to-end smoke test if available.

### Phase 4 — Audio ingestion and transcript pipeline
Goal:
Turn live audio into transcript events.

Tasks:
- Implement `audio.chunk` handling.
- Implement transcription adapter abstraction.
- Implement transcript repository.
- Emit `transcript.partial` and `transcript.final`.
- Render rolling transcript in agent UI.
- Handle transcript ordering and speaker attribution.

Suggested files:
- `backend/app/services/transcription.py`
- `backend/app/services/transcript_repository.py`
- `backend/tests/services/test_transcription.py`
- `backend/tests/ws/test_transcript_events.py`

Acceptance:
- Partial and final transcript events flow end to end.
- Agent UI shows rolling transcript updates.

### Phase 5 — Synthetic customer context and demo scenarios
Goal:
Support reusable synthetic demos.

Tasks:
- Create scenario fixtures for card declined, fee dispute, and travel notice.
- Implement CRM/scenario service for synthetic customer profiles.
- Attach scenario metadata to sessions.
- Display customer context in agent UI.

Suggested files:
- `data/fixtures/scenarios/*.json`
- `backend/app/services/crm_service.py`
- `backend/tests/services/test_crm_service.py`

Acceptance:
- Agent sees synthetic customer context on join.
- Scenario-specific context can be loaded reproducibly.

### Phase 6 — Corpus strategy and normalization pipeline
Goal:
Prepare corpora for retrieval.

Tasks:
- Define normalized schema for intent, policy, and FAQ corpora.
- Implement data cleaning, chunking, deduplication, and validation.
- Build normalizers for selected raw datasets.
- Author or curate a dedicated policy corpus for the POC.
- Produce processed JSONL outputs.

Suggested files:
- `pipeline/schemas/*.py`
- `pipeline/normalizers/*.py`
- `pipeline/jobs/build_corpora.py`
- `pipeline/tests/*`
- `data/processed/*.jsonl`

Acceptance:
- Intent, FAQ, and policy corpora are available in normalized form.
- Validation catches malformed records.
- Policy corpus exists explicitly rather than being implied.

### Phase 7 — Embeddings and vector indexing
Goal:
Convert processed corpora into searchable vector indexes.

Tasks:
- Implement embeddings abstraction.
- Implement vector store interface.
- Implement Chroma backend.
- Implement Pinecone backend as optional cloud profile.
- Implement indexing job.
- Implement reindex and reset utilities.

Suggested files:
- `backend/app/services/embeddings.py`
- `backend/app/services/vector_store/base.py`
- `backend/app/services/vector_store/chroma_store.py`
- `backend/app/services/vector_store/pinecone_store.py`
- `backend/app/services/vector_store/factory.py`
- `pipeline/jobs/build_index.py`

Acceptance:
- Indexes can be created from normalized corpora.
- Local development works with Chroma.
- Backend switching is configuration-driven.

Tests:
- Vector store factory tests.
- Index build tests.
- Retrieval smoke tests with fixture data.

### Phase 8 — Retrieval service and routing
Goal:
Support per-store semantic retrieval with normalized outputs.

Tasks:
- Implement retrieval service.
- Implement routing rules for intent, policy, and FAQ queries.
- Add result normalization with source metadata.
- Add filters and top-k support.

Suggested files:
- `backend/app/services/retrieval.py`
- `backend/tests/services/test_retrieval.py`
- `backend/tests/services/test_store_type_mapping.py`

Acceptance:
- Queries can target one or more logical stores.
- Results are normalized consistently.
- Retrieval routing is configurable and testable.

### Phase 9 — Realtime orchestrator integration
Goal:
Integrate retrieval into the live session loop safely.

Tasks:
- Implement session state store.
- Implement real-time orchestrator.
- Trigger retrieval from `transcript.final`.
- Add debounce and stale-task cancellation.
- Publish `retrieval.results` events.
- Keep the receive loop responsive.

Suggested files:
- `backend/app/services/session_state.py`
- `backend/app/services/realtime_orchestrator.py`
- `backend/tests/services/test_realtime_orchestrator.py`
- `backend/tests/ws/test_retrieval_integration.py`

Acceptance:
- Retrieval runs on final customer transcript events.
- Partial events do not trigger expensive retrieval by default.
- Newer transcript context supersedes stale inflight retrieval work.

### Phase 10 — Grounding and issue detection
Goal:
Assess evidence quality and assign safety states.

Tasks:
- Implement issue detection from transcript plus retrieval evidence.
- Implement grounding service.
- Detect missing policy support.
- Detect evidence conflicts.
- Publish issue updates and warnings.

Suggested files:
- `backend/app/services/grounding_service.py`
- `backend/tests/services/test_grounding_service.py`

Acceptance:
- The system can surface issue hypotheses.
- Unsupported operational guidance is downgraded or suppressed.

### Phase 11 — Recommendations and suggested responses
Goal:
Turn grounded evidence into useful agent assist outputs.

Tasks:
- Implement recommendation engine.
- Implement recommendation orchestrator.
- Generate issue hints, NBA cards, and suggested responses.
- Add duplicate suppression to avoid republishing unchanged outputs.
- Keep all outputs structured and evidence-linked.

Suggested files:
- `backend/app/services/recommendation_engine.py`
- `backend/app/services/recommendation_orchestrator.py`
- `backend/tests/services/test_recommendation_engine.py`
- `backend/tests/ws/test_recommendation_events.py`

Acceptance:
- Agent receives grounded recommendations when evidence supports them.
- Weak evidence produces warnings or low-confidence states.
- Suggestions remain editable and non-autonomous.

### Phase 12 — Summary and audit
Goal:
Generate end-of-call artifacts and audit history.

Tasks:
- Implement summary service.
- Generate overview, issues, actions, unresolved items, and case note draft.
- Persist summaries.
- Expose summary API.
- Implement audit event logging.

Suggested files:
- `backend/app/services/summary_service.py`
- `backend/app/services/audit_service.py`
- `backend/tests/services/test_summary_service.py`
- `backend/tests/services/test_audit_service.py`

Acceptance:
- Session end produces a summary.
- Audit events capture major system actions.

### Phase 13 — Replay and evaluation
Goal:
Measure quality and support regression testing.

Tasks:
- Implement transcript replay runner.
- Add golden scenarios.
- Capture outputs for issue detection, retrieval, grounding, recommendation, and summary.
- Add quality assertions and regression fixtures.

Suggested files:
- `backend/app/eval/replay_runner.py`
- `backend/app/eval/scenarios/*.json`
- `backend/tests/eval/*`

Acceptance:
- Scripted transcripts can run without live audio.
- Outputs can be compared against expected labels, states, and sources.

### Phase 14 — Demo polish and resilience
Goal:
Improve usability and demo stability.

Tasks:
- Improve loading, reconnect, and warning states.
- Add evidence panel polish.
- Add summary modal polish.
- Improve empty and failure states.
- Add replay mode UI toggle if useful.

Acceptance:
- Demo works reliably under normal local conditions.
- Failure states are understandable and recoverable.

### Phase 15 — Deployment profiles and operations
Goal:
Prepare the application for repeatable local and cloud-backed execution.

Tasks:
- Document local profile and cloud-assisted profile.
- Add environment-based backend switching.
- Add secrets/config handling guidance.
- Add structured logging and basic observability hooks.
- Document hosting requirements for WebSockets.

Acceptance:
- Application can be run locally from docs.
- Cloud-assisted mode has explicit configuration steps.

## 4. Cross-phase testing strategy

Testing layers:
- Unit tests for models, services, routing, grounding, and generation logic.
- Integration tests for API, WebSocket, transcript flow, retrieval flow, and summary flow.
- Replay tests for regression and scenario validation.
- UI smoke tests for agent and customer pages.

The implementation should avoid requiring live cloud services in core tests by using mocks and fixture data.

## 5. Coding assistant instructions

The coding assistant should:
- work phase by phase in dependency order,
- not assume any file exists unless created in an earlier phase,
- keep handlers thin and move logic into services,
- define explicit schemas before wiring flows,
- create tests alongside each phase,
- prefer the simplest working implementation that satisfies the spec.

The coding assistant should not:
- add telephony integrations,
- add real customer data,
- collapse all logic into the WebSocket handler,
- bypass grounding for operational recommendations,
- create autonomous customer-facing execution paths. [file:577]

## 6. Final milestone definition

The project is considered complete when:
- a customer and an agent can join a browser voice session,
- live transcript is shown,
- synthetic customer context is shown,
- retrieval-backed grounded recommendations are generated safely,
- evidence is visible,
- summary artifacts are generated at session end,
- replay and evaluation flows exist,
- the system runs locally with documented setup. [file:575][file:576][file:577]