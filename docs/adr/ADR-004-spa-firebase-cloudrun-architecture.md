# ADR-004: Pure SPA Architecture on Firebase Hosting with Cloud Run WebSocket Gateway

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board
* **Context**: Technical Specification §2.4, Checkpoint D2

---

## Context & Problem Statement
Contact center agent interfaces require instant startup, immediate responsiveness, and continuous bidirectional WebSocket connectivity. Frameworks employing Server-Side Rendering (Next.js / Remix) introduce hydration overhead, server-side Node.js memory bloat, and operational complexity when managing persistent stateful WebSocket connections across SSR pods.

## Decision
We implemented a **decoupled SPA + ASGI Gateway architecture**:
1. **Frontend**: Pure Single Page Application (SPA) built with **Vite 6 + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui**, packaged into static assets (`apps/web/dist`).
2. **Hosting**: Deployed globally to **Firebase Hosting CDN**, providing instant edge asset delivery with zero server maintenance.
3. **Backend Gateway**: Python 3.14 + **FastAPI + Uvicorn** running on **Cloud Run** with Session Affinity (`sessionAffinity: true`) and a 3,600s WebSocket connection timeout.

## Consequences

### Positive
* **Zero Hydration Overhead**: The agent cockpit boots instantly without client-server markup mismatches or hydration delay.
* **Cost & Scalability**: Static assets scale infinitely via Google's edge CDN without consuming compute cycles on Cloud Run.
* **Separation of Concerns**: The frontend team works independently in `apps/web/` using mock JSON events while the backend team iterates on the FastAPI pipeline.

### Negative / Trade-offs
* Search Engine Optimization (SEO) is client-rendered (acceptable as this is a private authenticated enterprise cockpit).
