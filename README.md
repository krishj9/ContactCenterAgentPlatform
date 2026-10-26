# Contact Center Agent Helper Platform

Enterprise Contact Center Agent Assist platform supporting real-time audio transcription, classifier-based intent detection, and grounded next-best action guidance using hybrid policy RAG.

[![Python 3.14.8](https://img.shields.io/badge/python-3.14.8-blue.svg)](https://www.python.org/downloads/release/python-3140/)
[![uv](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://github.com/astral-sh/uv)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/frontend-React%2019-blue.svg)](https://react.dev)
[![PostgreSQL 16](https://img.shields.io/badge/vector%20store-pgvector-blue.svg)](https://github.com/pgvector/pgvector)
[![WCAG 2.1 AA](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-green.svg)](https://www.w3.org/WAI/WCAG21/quickref/)

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph Browser ["Web Browser SPA (Vite + React 19)"]
        CV["Customer View (/customer)<br/>AudioWorklet 16kHz PCM"]
        AC["Agent Cockpit (/agent)<br/>Assist Cards + Feedback"]
    end

    subgraph Edge ["Edge & Security"]
        CDN["Firebase Hosting CDN"]
        IAP["Cloud Armor WAF + IAP"]
        VPC_SC["VPC Service Controls Perimeter"]
    end

    subgraph Backend ["FastAPI Gateway (Cloud Run)"]
        WS["WebSocket Session Manager"]
        DLP["Cloud DLP Redactor"]
        MA["Model Armor Defense"]
        ORCH["Realtime Orchestrator"]
        OTEL["OpenTelemetry Tracer"]
    end

    subgraph Data ["Data & AI Services (CMEK Encrypted)"]
        STT["Speech-to-Text V2"]
        INTENT["Vertex AI Intent Classifier<br/>(Gemma 3 1B LoRA on L4 GPU)"]
        PG["Cloud SQL PostgreSQL 16<br/>(pgvector HNSW + tsvector)"]
        LLM["Vertex AI Gemini 3.8 Flash<br/>(Grounded Generator)"]
        REDIS["Memorystore Redis 7<br/>(Session State & Pub/Sub)"]
    end

    CDN -.->|Static Assets| Browser
    CV <-->|WSS 16kHz Audio| IAP
    AC <-->|WSS Internal Assist| IAP
    IAP --> WS
    WS --> DLP
    WS --> MA
    WS --> ORCH
    ORCH --> STT
    ORCH -->|Fast Path ≤ 60ms| INTENT
    ORCH -->|Hybrid Search| PG
    ORCH -->|Assist Path ≤ 1.5s| LLM
    ORCH <--> REDIS
    OTEL -.->|W3C Traceparent| Backend
```

---

## 2. Core Technology Stack & Standards

| Layer | Technology | Details |
|---|---|---|
| **Python Runtime** | **Python 3.14.8** | Pinned via `.python-version` and `pyproject.toml`. |
| **Package Manager** | **uv** | Fast, deterministic packaging (`uv venv`, `uv pip`, `uv run`). |
| **Backend API** | **FastAPI + Uvicorn** | Async-first architecture with strict Pydantic v2 event contracts. |
| **Frontend Framework** | **Vite 6 + React 19 + TypeScript** | Pure SPA architecture deployed to Firebase Hosting CDN. |
| **Styling & UI** | **Tailwind CSS v4 + shadcn/ui** | Accessible components complying with WCAG 2.1 AA standards. |
| **Audio Capture** | **Web Audio API + AudioWorklet** | `pcm-recorder-worklet.js` downsampling to 16kHz mono linear PCM. |
| **Vector Store** | **PostgreSQL 16 (pgvector)** | HNSW vector index + `tsvector` hybrid search with Reciprocal Rank Fusion. |
| **Intent Classifier** | **Fine-Tuned Gemma 3 1B LoRA** | Single-pass linear classifier head (p95 latency < 60ms). |
| **Observability** | **OpenTelemetry + Prometheus** | W3C distributed trace propagation (`traceparent`), Cloud Trace, Grafana. |
| **Security & Privacy** | **VPC-SC + Cloud KMS (CMEK)** | Cloud DLP PII redaction and Model Armor prompt defense. |

---

## 3. Local Development Quickstart

### Prerequisites
* macOS / Linux with [uv](https://github.com/astral-sh/uv) (>= 0.4.0) and [Node.js](https://nodejs.org/) (>= 20).
* Docker Desktop or Podman for containerized databases and services.

---

### Option A: All-in-One Docker Stack (Recommended for Evaluation)
Launches the full containerized environment (PostgreSQL pgvector, Redis, API, and Web UI) with a single command:

```bash
# Launch core application stack
docker compose -f infra/compose/docker-compose.yml up -d

# (Optional) Launch local observability stack (OTel Collector, Jaeger, Prometheus, Grafana, Loki)
docker compose -f infra/compose/docker-compose.obs.yml up -d
```
* **Web UI**: [http://localhost:3000](http://localhost:3000)
* **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Grafana Dashboards**: [http://localhost:3001](http://localhost:3001) (`admin`/`admin`)
* **Jaeger Tracing**: [http://localhost:16686](http://localhost:16686)

---

### Option B: Local Development with Hot Reloading (Recommended for Coding)

#### 1. Start Backing Infrastructure (Docker)
Start only the stateful backing services:
```bash
# Start PostgreSQL pgvector, Redis, and Fake GCS
docker compose -f infra/compose/docker-compose.yml up -d postgres redis fake-gcs-server

# Run database migrations
CC_APP_PROFILE=local uv run alembic -c backend/alembic.ini upgrade head
```

#### 2. Start Backend API Server
```bash
# Pin and create Python virtual environment
uv venv --python 3.14.8 .venv
source .venv/bin/activate

# Install all workspace dependencies and dev tools
uv sync

# Run backend with live reload on http://localhost:8000
uv run uvicorn backend.app.main:app --reload --port 8000
```

#### 3. Start Frontend Development Server
In a separate terminal:
```bash
cd apps/web
npm install
npm run dev
# Vite dev server running on http://localhost:3000
```

#### 4. Testing & Code Quality
```bash
# Run offline unit and integration test suite
uv run pytest backend/tests/ -v

# Run linter and formatter
uv run ruff check .
uv run ruff format .
```

---

## 4. Strict Architectural Invariants

1. **Human-in-the-Loop (R14)**:
   * The platform strictly provides *assistive guidance*.
   * It **never** auto-speaks, auto-sends messages to customers, or auto-executes financial banking actions (e.g., fee waivers, card unlocks). All guidance is presented as editable suggestions.
2. **Customer Isolation (R9)**:
   * Customer WebSocket connections are cryptographically restricted to public dialogue events (`session.ready`, `transcript.final`, `transcript.partial`, `session.end`).
   * Internal assist events (`issue.update`, `assist.recommendation`, `guardrail.warning`) are filtered out at the transport layer.
3. **Grounding Safety (R10, R13)**:
   * No recommendation may be presented as `GROUNDED` without supporting evidence from the policy store.
   * If evidence is missing or similarity score is below threshold, output is marked `POLICY_REVIEW_NEEDED` with `MISSING_EVIDENCE`.
4. **Offline Test Isolation**:
   * Unit tests run completely offline without relying on external cloud APIs or live vector databases (`pytest-socket` enforced).

---

## 5. Testing & Verification Suites

| Test Suite | Purpose | Execution Command |
|---|---|---|
| **Unit & Contract Tests** | Pydantic event contracts, domain ports, and DI containers | `uv run pytest backend/tests/ports/ backend/tests/contracts/` |
| **Offline RAG & Invariant Tests** | Grounding verification, policy chunking, and taxonomy rules | `uv run pytest backend/tests/invariants/ backend/tests/pipeline/` |
| **GenAI Quality Evaluation** | Vertex GenAI evaluation and nightly golden scenario replays | `uv run python -m eval.jobs.nightly` |
| **Prompt Injection Red-Team** | Model Armor defense against adversarial injection vectors | `uv run pytest backend/tests/security/injection/` |
| **Chaos Resilience Drills** | Service outage and fallback state machine drills | `uv run pytest backend/tests/chaos/` |
| **High-Concurrency Load Test** | k6 WebSocket test simulating 500 concurrent live sessions | `k6 run tests/load/k6_websocket_call.js` |

---

## 6. Architecture Decision Records (ADRs)

Key architectural decisions are documented in [`docs/adr/`](./docs/adr/):
* [**ADR-001**](./docs/adr/ADR-001-intent-classifier-vs-pure-rag.md): Classifier-Based Intent Detection vs. Pure RAG
* [**ADR-002**](./docs/adr/ADR-002-audioworklet-pcm-streaming.md): Realtime Streaming Audio over AudioWorklet 16kHz PCM
* [**ADR-003**](./docs/adr/ADR-003-hybrid-retrieval-pgvector.md): Hybrid Vector Search using PostgreSQL 16 pgvector
* [**ADR-004**](./docs/adr/ADR-004-spa-firebase-cloudrun-architecture.md): Pure SPA Architecture on Firebase Hosting with Cloud Run Gateway
* [**ADR-005**](./docs/adr/ADR-005-opentelemetry-w3c-tracing.md): End-to-End W3C Distributed Tracing via OpenTelemetry
* [**ADR-006**](./docs/adr/ADR-006-human-in-the-loop-invariant.md): Human-in-the-Loop Assist Invariant (Strict Rule R14)
* [**ADR-007**](./docs/adr/ADR-007-customer-isolation-filter.md): Outbound Event Customer Isolation Filter (Strict Rule R9)
* [**ADR-008**](./docs/adr/ADR-008-vpc-sc-and-cmek-security.md): VPC Service Controls & Customer-Managed Encryption Keys (CMEK)

---

## 7. Production Operations & Runbooks

Operational procedures are documented in [`docs/runbooks/`](./docs/runbooks/):
* [**Incident Response Protocol**](./docs/runbooks/incident_response.md): Severity levels, paging, and triage checklists.
* [**High-Latency Troubleshooting**](./docs/runbooks/high_latency_troubleshooting.md): Diagnosing p95 latency spikes (> 2.5s) via Cloud Trace.
* [**Database Failover & Recovery**](./docs/runbooks/database_failover.md): Cloud SQL multi-zone failover and read replica promotion.
* [**Model Rollback Playbook**](./docs/runbooks/model_rollback.md): Vertex AI intent model traffic splitting and instant canary rollback.
* [**Disaster Recovery Plan**](./docs/runbooks/disaster_recovery.md): Cross-region recovery procedures achieving RPO < 15 min and RTO < 60 min.
* [**Capacity & Scaling Analysis**](./docs/capacity.md): Hardware, network, and memory sizing for 500 to 2,000 concurrent sessions.
