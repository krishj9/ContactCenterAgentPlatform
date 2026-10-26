# AGENTS.md — Development Guidelines & Environment Standards

This document establishes the architectural principles, environment constraints, and runtime rules for AI agents and developers working on the Contact Center Agent Helper platform.

---

## 1. Core Technology Stack & Environment

All development must strictly adhere to the following stack:

| Component | Standard / Version | Tooling & Notes |
|---|---|---|
| **Python Runtime** | **Python 3.14.8** | Pinned via `.python-version`. Must use `/Users/krishnajammula/.local/share/uv/python/cpython-3.14-macos-aarch64-none/bin/python3.14` or `uv python pin 3.14.8`. |
| **Package & Env Manager** | **uv** | Never use raw `pip` or virtualenv. Always use `uv venv`, `uv sync`, `uv run`, `uv add`. |
| **Backend Framework** | **FastAPI** | Async-first architecture, Pydantic v2 strict schema validation, Uvicorn ASGI server. |
| **Frontend Framework** | **Vite 6 + React 19 + TypeScript** | Pure SPA architecture in `apps/web/`, zero SSR hydration overhead. |
| **UI Components & Styling** | **Tailwind CSS v4 + shadcn/ui** | Radix UI primitives, Lucide React icons, dark/light theme support. |
| **State Management** | **Zustand v5 + TanStack Query v5** | Zustand for transient WebSocket streams & audio; TanStack Query for server cache. |
| **Frontend Hosting** | **Firebase Hosting** | Global CDN serving Vite SPA static assets; connects directly to FastAPI Cloud Run backend via WSS/HTTPS. |
| **Audio Capture** | **Web Audio API + AudioWorklet** | `pcm-recorder-worklet.js` downsampling browser microphone to 16kHz mono 16-bit linear PCM. |
| **Persistence & Cache** | **PostgreSQL 16 (pgvector) + Redis 7** | SQLAlchemy 2.0 async + asyncpg + Alembic migrations; Redis for session states and pub/sub. |
| **Vector & RAG** | **PostgreSQL 16 pgvector (Local & Cloud SQL)** | Unified local/GCP vector store with HNSW indexing, full-text `tsvector` hybrid retrieval (RRF), and strict policy chunk lineage. |
| **Intent Detection** | **Fine-tuned Gemma 3 1B LoRA** | Single-pass linear classifier head (ONNX Runtime int8 serving locally, Vertex AI Endpoints on GCP). |

---

## 2. Command Reference & Virtual Environment Rules

Always invoke tools using `uv`:

```bash
# Create and activate virtual environment with Python 3.14.8
uv venv --python 3.14.8 .venv
source .venv/bin/activate

# Install dependencies and dev tools
uv sync

# Run backend development server
uv run uvicorn backend.app.main:app --reload --port 8000

# Run linter & formatter
uv run ruff check .
uv run ruff format .

# Run test suite
uv run pytest backend/tests/ -v

# Frontend development
cd apps/web && npm install && npm run dev
```

---

## 3. Strict Architectural Invariants

AI agents and contributors must uphold these invariants in all PRs and code changes:

1. **Human-in-the-Loop (R14)**:
   - The platform strictly provides *assistive guidance* to human agents.
   - The system must **never** auto-speak, auto-send messages to customers, or auto-execute banking actions (e.g., fee waivers, card unblocks).
   - All recommendations must be presented as editable suggestions.

2. **Grounding Safety (R10, R13)**:
   - No operational next-best action may be presented as `GROUNDED` without supporting evidence from the **Policy Store**.
   - If policy evidence is absent or similarity is below threshold, output must be marked `POLICY_REVIEW_NEEDED` or suppressed (`MISSING_EVIDENCE`).
   - Every generated recommendation step must cite an exact chunk ID verified against retrieval context.

3. **Customer Isolation (R9, R14)**:
   - Customer WebSocket connections must never receive internal assist events (`issue.update`, `recommendation.update`, `response_suggestion.update`, `guardrail.warning`).
   - The `/customer` UI view must strictly display the voice/chat interface and conversation transcript without internal assist metadata.

4. **Offline Test Isolation**:
   - Unit tests must be completely runnable offline without relying on external cloud APIs or live vector databases (`pytest-socket` enforced).

---

## 4. Documentation References

Before implementing features or modifying pipelines, review:
* [`docs/technical_specification.md`](./docs/technical_specification.md): Complete architecture specification, GCP mappings, and mathematical calibration thresholds.
* [`docs/implementation_plan.md`](./docs/implementation_plan.md): 11-phase delivery plan (P0 to P10) with exact exit criteria.
* [`agent/TASKS.md`](./agent/TASKS.md): Active task checklist tracking Phase P0 through P10.
