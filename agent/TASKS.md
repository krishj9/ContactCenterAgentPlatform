# Agent Task Tracker — Production Rebuild Plan

This tracker reflects the production rebuild plan defined in [`docs/implementation_plan.md`](../docs/implementation_plan.md).

---

## Rebuild Progress (P0 – P10)

| Phase | Description | Track | Status | Primary Output |
|---|---|---|---|---|
| **P0** | Hygiene & Baseline | App + ML | ✅ COMPLETED | Security tooling (gitleaks/ruff), Python 3.14.8, baseline setup, golden scenarios |
| **P1** | Contracts, Ports & Dependency Injection | App | ✅ COMPLETED | Pydantic v2 / TypeScript event contracts, DI container |
| **P2** | Local Platform, UI Scaffold & Persistence | App | ✅ COMPLETED | Docker Compose, PostgreSQL 16 (pgvector), Vite + React 19 + shadcn/ui |
| **P3** | Knowledge Pipeline & Policy Corpus | App | ⬜ READY TO START | Markdown policy corpus, PostgreSQL pgvector index, manifest guard |
| **P4** | Intent Model: Training & Serving | ML | ⬜ TODO | Fine-tuned Gemma 3 1B LoRA classifier, ONNX Runtime int8 serving |
| **P5** | RAG v2, Grounding & UI Assist Cards | App + ML | ⬜ TODO | Router, reranker, NLI verifier, NBA & Suggested Response cards |
| **P6** | Realtime Voice, Security & Cockpit Polish | App | ⬜ TODO | AudioWorklet PCM 16kHz, JWT signed tokens, 3-column cockpit |
| **P7** | GCP Infrastructure, Terraform & Adapters | Platform | ⬜ TODO | Terraform modules, Cloud Run, Vertex AI, dev deployment |
| **P8** | ML/KB Pipelines & CI/CD Release Trains | ML + Platform | ⬜ TODO | Vertex AI Pipelines (KFP v2), automated promotion & rollback |
| **P9** | Observability, Telemetry & GenAI Eval | Platform + ML | ⬜ TODO | OpenTelemetry, Vertex Gen AI Eval, Cloud Monitoring SLOs |
| **P10**| Production Hardening, Security & Load Test | All | ⬜ TODO | VPC Service Controls, DLP PII redaction, k6 500-session load test |

---

## Detailed Task Breakdown

### Phase P0: Hygiene & Baseline
- [x] **P0.1**: Configure `gitleaks` secret scanning + `ruff` pre-commit hooks and CI workflow step.
- [x] **P0.2**: Pin Python 3.14.8 across `pyproject.toml`, CI workflow, and Dockerfiles.
- [x] **P0.3**: Standardize package imports to `app.*` with `backend/` as root directory.
- [x] **P0.4**: Configure `CorpusPaths` and set `MAX_RECORDS_PER_STORE=0` (unlimited).
- [x] **P0.5**: Create golden scenario fixtures (`eval/scenarios/*.json`).
- [x] **P0.6**: Set up baseline measurement harness and record report (`eval/reports/baseline.md`).
- [x] **P0.7**: Formally amend requirements R8/R9 in `docs/requirements.md`.

### Phase P1: Contracts, Ports & DI
- [x] **P1.1**: Versioned event contracts (Pydantic v2 models with discriminated union).
- [x] **P1.2**: Core domain models (`IntentPrediction`, `EvidenceChunk`, `NextBestAction`, etc.).
- [x] **P1.3**: Backend ports (`IntentClassifier`, `VectorIndex`, `Generator`, `SpeechToText`).
- [x] **P1.4**: TypeScript contract types generated for the Vite client.
- [x] **P1.5**: Zustand store interfaces (`useSessionStore`, `useTranscriptStore`, `useAssistStore`).
- [x] **P1.6**: Test adapters for offline mock testing.
- [x] **P1.7**: Settings configuration and dependency injection container.
- [x] **P1.8**: Transcript replay runner for automated regression testing.
- [x] **P1.9**: Strict mypy setup and `pytest-socket` offline isolation.

### Phase P2: Local Platform, UI Scaffold & Persistence
- [x] **P2.1**: Docker Compose `core` (api, web, postgres:16 with pgvector, redis, fake-gcs).
- [x] **P2.2**: Scaffold Vite 6 + React 19 + TypeScript SPA in `apps/web/`.
- [x] **P2.3**: Install and configure Tailwind CSS v4 + shadcn/ui component library.
- [x] **P2.4**: Client routing (`/customer` and `/agent`) and shell layouts.
- [x] **P2.5**: Alembic database schema migrations for all entities.
- [x] **P2.6**: PostgreSQL repositories (SQLAlchemy 2.0 async + asyncpg).
- [x] **P2.7**: Redis session state store (turn window, task cancellation locks).
- [x] **P2.8**: Structured audit event logger persisting to database.
- [x] **P2.9**: Production Dockerfiles for `apps/api` and `apps/web`.
- [x] **P2.10**: Developer Makefile commands (`make up`, `make up-mock`, `make seed`).

### Phase P3: Knowledge Pipeline & Policy Corpus
- [x] **P3.1**: Intent taxonomy registry (`taxonomy/intents.yaml`) and alias mappings.
- [x] **P3.2**: Policy authoring schema and CODEOWNERS compliance review workflow.
- [x] **P3.3**: Author initial POC policy corpus in Markdown.
- [x] **P3.4**: Heading-aware Markdown chunker.
- [x] **P3.5**: FAQ semantic intent tagging.
- [x] **P3.6**: Medallion pipeline layout (raw → normalized → chunks → embeddings).
- [x] **P3.7**: Corpus manifest generator and startup guard check.
- [x] **P3.8**: Local `EmbeddingGemma` adapter with query/document prefixes.
- [x] **P3.9**: PostgreSQL pgvector adapter with dense (HNSW) + full-text (`tsvector`) hybrid search and active version routing.
- [x] **P3.10**: Indexing jobs (`kb_build`, `kb_promote`, `kb_upsert`).
- [x] **P3.11**: Data quality assertion suite.
- [x] **P3.12**: Retrieval evaluation harness measuring Recall@k and nDCG@5.


### Phase P4: Intent Model: Training & Serving
- [x] **P4.1**: Dataset preparation (Banking77, CLINC150 OOS, synthetic conversational noise).
- [x] **P4.2**: Conversational multi-turn spoken dialogue augmentation.
- [x] **P4.3**: LoRA fine-tuning pipeline on Gemma 3 1B with class weights.
- [x] **P4.4**: Temperature calibration on validation set and ambiguity decision layer.
- [x] **P4.5**: Model evaluation against Spec §3.2.4 quality gates.
- [x] **P4.6**: Execute initial training run and verify Champion criteria.
- [x] **P4.7**: Merge LoRA and export to ONNX Runtime int8.
- [x] **P4.8**: Build `apps/intent-svc` microservice container.
- [x] **P4.9**: Backend client adapter with exemplar-kNN fallback.
- [x] **P4.10**: Connect intent classification to orchestrator with 300ms debounce.
- [x] **P4.11**: Build Agent UI Intent Chip and "Why?" 3-exemplar drawer.

### Phase P5: RAG v2, Grounding & UI Assist Cards
- [x] **P5.1**: Multi-turn query builder with intent description synthesis.
- [x] **P5.2**: Store router with parallel dispatch and filter-relax retry.
- [x] **P5.3**: Cross-encoder reranker adapter (`bge-reranker-v2-m3`).
- [x] **P5.4**: Calibrate evidence and policy thresholds from qrels.
- [x] **P5.5**: Structured Pydantic generation schemas with citation constraints.
- [x] **P5.6**: Local Ollama Gemma 3 generator adapter with JSON-schema mode.
- [x] **P5.7**: Claim and citation verifier (chunk ID verification + NLI entailment).
- [x] **P5.8**: Deterministic Grounding State Machine.
- [x] **P5.9**: Structured playbook YAML fallback templates.
- [x] **P5.10**: Invariant test suite verifying zero ungrounded actions.
- [x] **P5.11**: Summary Service v2 generating structured case notes.
- [x] **P5.12**: UI Grounding Banner component with dynamic status coloring.
- [x] **P5.13**: UI Next-Best Action Cards with step checklists and action-type tags.
- [x] **P5.14**: UI Suggested Response Card with 1-click copy/insert/edit.
- [x] **P5.15**: UI Collapsible Evidence Drawer with matched snippets and similarity scores.
- [x] **P5.16**: UI Post-Call Summary Modal.

### Phase P6: Realtime Voice, Security & Cockpit Polish
- [x] **P6.1**: Signed JWT join tokens with Redis `jti` single-use tracking.
- [x] **P6.2**: Outbound event filter ensuring customers never receive internal assist data.
- [x] **P6.3**: Multi-instance Redis Pub/Sub broadcast.
- [x] **P6.4**: Web Audio API AudioWorklet (`pcm-recorder-worklet.js`) downsampling to 16kHz mono PCM.
- [x] **P6.5**: Local Faster-Whisper streaming speech-to-text adapter with VAD.
- [x] **P6.6**: Customer View (`/customer`) with animated audio waveform canvas.
- [x] **P6.7**: 3-column Agent Cockpit layout assembly (`/agent`).
- [x] **P6.8**: Live rolling transcript timeline with partial styling and keyword search.
- [x] **P6.9**: Customer Context & synthetic CRM history panel.
- [x] **P6.10**: Audio connection resilience, sequence gap tracking, and auto-reconnect.

### Phase P7: GCP Infrastructure, Terraform & Cloud Adapters
- [x] **P7.1**: Terraform core modules (project, remote state, artifact registry, KMS).
- [x] **P7.2**: Workload Identity Federation for GitHub Actions.
- [x] **P7.3**: VPC networking, NAT, Serverless VPC Access / Direct VPC Egress for Cloud Run, Private Service Access.
- [x] **P7.4**: Cloud SQL PostgreSQL 16 with pgvector extension enabled and Memorystore Redis provisioning.
- [x] **P7.5**: Firebase Hosting provisioning & distribution setup for Vite SPA static dist.
- [x] **P7.6**: Vertex AI Intent Endpoint provisioning with L4 GPU.
- [x] **P7.7**: Cloud Run API Gateway deployment (`api` with session affinity, 3600s WebSocket timeout, min instances ≥ 1).
- [x] **P7.8**: Cloud Armor WAF and Identity-Aware Proxy (IAP) guarding agent routes.
- [x] **P7.9**: GCP port adapters (Vertex embeddings, Cloud SQL pgvector, Ranking, Gemini Flash, STT V2).
- [x] **P7.10**: Cloud Run Job for knowledge base indexing into Cloud SQL PostgreSQL pgvector.
- [x] **P7.11**: Deploy complete Dev environment (`envs/dev`).

### Phase P8: ML & Knowledge Pipelines, CI/CD Release Trains
- [x] **P8.1**: KFP `intent_train` Vertex AI Pipeline.
- [x] **P8.2**: Model promotion traffic splitting and alias management.
- [x] **P8.3**: KFP `kb_build` knowledge base pipeline with automated alias flip.
- [x] **P8.4**: GitHub Actions triggers for policy updates and taxonomy changes.
- [x] **P8.5**: Application CI/CD pipeline with Cosign image signing.
- [x] **P8.6**: Binary Authorization policy enforcement.
- [x] **P8.7**: Provision Staging and Production environments (`envs/staging`, `envs/prod`).

### Phase P9: Observability, Telemetry & GenAI Eval
- [ ] **P9.1**: OpenTelemetry distributed tracing from Vite SPA to backend and LLM calls.
- [ ] **P9.2**: Local observability profile (Jaeger, Prometheus, Grafana, Loki).
- [ ] **P9.3**: Cloud Monitoring SLO alerts and golden signal dashboards.
- [ ] **P9.4**: Audit log sinks streaming to BigQuery and locked GCS bucket.
- [ ] **P9.5**: Vertex AI GenAI Evaluation pipeline (groundedness, safety, policy adherence).
- [ ] **P9.6**: Nightly automated quality evaluation job.
- [ ] **P9.7**: Vertex AI Model Monitoring for drift detection on the intent endpoint.
- [ ] **P9.8**: Agent UI feedback capture widgets streaming telemetry to BigQuery.

### Phase P10: Production Hardening, Security & Load Testing
- [ ] **P10.1**: VPC Service Controls perimeter around all data and AI services.
- [ ] **P10.2**: Customer-Managed Encryption Keys (CMEK) via Cloud KMS.
- [ ] **P10.3**: Cloud DLP real-time PII inspection and redaction.
- [ ] **P10.4**: Model Armor prompt injection protection layer.
- [ ] **P10.5**: Adversarial prompt injection red-team test suite.
- [ ] **P10.6**: k6 high-concurrency WebSocket load test (500 concurrent sessions).
- [ ] **P10.7**: Chaos resilience drills testing component failure modes.
- [ ] **P10.8**: WCAG 2.1 AA accessibility audit and keyboard navigation certification.
- [ ] **P10.9**: Architecture Decision Records (ADRs) and production operational runbooks.
