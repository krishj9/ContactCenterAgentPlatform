# ADR-005: End-to-End W3C Distributed Tracing via OpenTelemetry

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board
* **Context**: Technical Specification §5.4, Phase P9.1

---

## Context & Problem Statement
A single user interaction in the contact center spans multiple asynchronous hops: browser AudioWorklet $\rightarrow$ WebSocket gateway $\rightarrow$ Speech-to-Text $\rightarrow$ Intent Classifier $\rightarrow$ pgvector retrieval $\rightarrow$ Gemini LLM. When an assist recommendation is delayed or ungrounded, debugging without cross-boundary distributed tracing requires piecing together fragmented logs across disconnected services.

## Decision
We standardized on the **W3C Trace Context specification** (`traceparent: 00-${traceId}-${spanId}-01`) propagated across all client and backend layers:
1. **Browser Inception**: The Vite SPA generates the root trace context (`apps/web/src/telemetry/otel.ts`) and passes `traceparent` as a query parameter during the WebSocket handshake.
2. **Context Propagation**: The FastAPI gateway maintains span context in Python `contextvars`, propagating parent IDs across all async tasks, database queries, and Vertex AI API invocations.
3. **Telemetry & SLOs**: `TelemetryManager` records span durations into Prometheus metrics and Golden Signal histograms.
4. **Cloud Trace Export**: Traces are exported to Google Cloud Trace in production and Jaeger locally via the OpenTelemetry Collector.

## Consequences

### Positive
* **Single Pane of Glass**: Engineers can click any trace in Cloud Trace and view the exact timeline from customer speech to LLM output.
* **Accurate SLO Metrics**: Latency budgets (p95 < 2.5s) are tracked across end-to-end user transactions rather than isolated backend hops.

### Negative / Trade-offs
* Minor byte overhead on WebSocket frames and carrier dictionaries to pass trace context headers.
