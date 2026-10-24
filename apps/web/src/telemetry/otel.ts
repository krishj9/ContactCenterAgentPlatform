/// <reference types="vite/client" />

/**
 * OpenTelemetry W3C Distributed Trace Propagation for Vite React SPA (Phase P9.1).
 *
 * Links user browser clicks, audio capture, and WebSocket events into end-to-end
 * distributed traces propagating to Cloud Trace / Jaeger via W3C `traceparent` headers.
 */

export interface ClientSpan {
  name: string;
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  startTime: number;
  attributes: Record<string, string | number | boolean>;
}

// Generate random 16-byte (32-character hex) trace ID
export function generateTraceId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

// Generate random 8-byte (16-character hex) span ID
export function generateSpanId(): string {
  const bytes = new Uint8Array(8);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

// Format W3C traceparent header: 00-{trace_id}-{span_id}-01
export function createTraceparent(traceId?: string, spanId?: string): string {
  const tId = traceId || generateTraceId();
  const sId = spanId || generateSpanId();
  return `00-${tId}-${sId}-01`;
}

// Parse W3C traceparent header
export function parseTraceparent(header: string): { traceId: string; spanId: string; flags: string } | null {
  const match = header.match(/^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/);
  if (!match) return null;
  return {
    traceId: match[1],
    spanId: match[2],
    flags: match[3],
  };
}

let activeSessionTraceId: string | null = null;

export function getOrCreateSessionTraceId(): string {
  if (!activeSessionTraceId) {
    activeSessionTraceId = generateTraceId();
  }
  return activeSessionTraceId;
}

export function resetSessionTraceId(): void {
  activeSessionTraceId = null;
}

const activeSpans: Map<string, ClientSpan> = new Map();

export function startClientSpan(name: string, attributes: Record<string, string | number | boolean> = {}): ClientSpan {
  const traceId = getOrCreateSessionTraceId();
  const spanId = generateSpanId();
  const span: ClientSpan = {
    name,
    traceId,
    spanId,
    startTime: performance.now(),
    attributes: {
      'browser.user_agent': navigator.userAgent,
      'app.component': 'web-spa',
      ...attributes,
    },
  };
  activeSpans.set(spanId, span);
  return span;
}

export function endClientSpan(span: ClientSpan, additionalAttributes: Record<string, string | number | boolean> = {}): void {
  const duration = performance.now() - span.startTime;
  span.attributes = {
    ...span.attributes,
    ...additionalAttributes,
    'duration_ms': Math.round(duration * 100) / 100,
  };
  activeSpans.delete(span.spanId);

  // In production / GCP, this can export to OTel HTTP collector (/v1/traces)
  if (import.meta.env?.DEV) {
    console.debug(`[OTel Span] ${span.name} (00-${span.traceId}-${span.spanId}-01) finished in ${duration.toFixed(2)}ms`);
  }
}
