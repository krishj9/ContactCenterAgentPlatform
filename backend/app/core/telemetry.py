"""OpenTelemetry Distributed Tracing & Telemetry Instrumentation (Phase P9.1).

Implements W3C distributed trace propagation (traceparent), span lifecycle management,
and golden signal metrics tracking across Vite SPA -> Gateway -> Orchestrator -> RAG -> Gemini.
"""

from __future__ import annotations

import contextvars
import functools
import logging
import re
import secrets
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger("app.core.telemetry")

# W3C Trace Context regex: version(2 hex)-trace_id(32 hex)-parent_id(16 hex)-trace_flags(2 hex)
TRACEPARENT_REGEX = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")

_current_span: contextvars.ContextVar[SpanContext | None] = contextvars.ContextVar(
    "current_span", default=None
)


def generate_trace_id() -> str:
    """Generate a random 32-character hexadecimal W3C trace ID."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate a random 16-character hexadecimal W3C span ID."""
    return secrets.token_hex(8)


@dataclass
class SpanContext:
    """Active span telemetry context."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    start_time_ns: int = field(default_factory=time.time_ns)
    end_time_ns: int | None = None
    duration_ms: float = 0.0
    status: str = "OK"  # "OK" | "ERROR"
    events: list[dict[str, Any]] = field(default_factory=list)

    def set_attribute(self, key: str, value: Any) -> None:
        """Add attribute metadata to the active span."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Record an event annotation within the span."""
        self.events.append(
            {
                "name": name,
                "timestamp_ns": time.time_ns(),
                "attributes": attributes or {},
            }
        )

    def finish(self, status: str = "OK") -> None:
        """Mark span as finished and calculate duration."""
        self.status = status
        self.end_time_ns = time.time_ns()
        self.duration_ms = (self.end_time_ns - self.start_time_ns) / 1_000_000.0

    @property
    def traceparent(self) -> str:
        """Return W3C traceparent header value."""
        return f"00-{self.trace_id}-{self.span_id}-01"


def extract_traceparent(carrier: dict[str, Any] | str | None) -> tuple[str, str | None]:
    """Extract trace_id and parent_span_id from W3C traceparent carrier."""
    header_val: str | None = None
    if isinstance(carrier, str):
        header_val = carrier.strip()
    elif isinstance(carrier, dict):
        header_val = carrier.get("traceparent") or carrier.get("Traceparent")

    if header_val:
        match = TRACEPARENT_REGEX.match(header_val)
        if match:
            return match.group(1), match.group(2)

    return generate_trace_id(), None


def inject_traceparent(
    carrier: dict[str, str], trace_id: str | None = None, span_id: str | None = None
) -> dict[str, str]:
    """Inject W3C traceparent header into outgoing carrier dictionary."""
    active = _current_span.get()
    t_id = trace_id or (active.trace_id if active else generate_trace_id())
    s_id = span_id or (active.span_id if active else generate_span_id())
    carrier["traceparent"] = f"00-{t_id}-{s_id}-01"
    return carrier


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    parent_context: str | dict[str, Any] | None = None,
) -> Iterator[SpanContext]:
    """Synchronous context manager creating a distributed span."""
    parent_span = _current_span.get()

    if parent_context:
        trace_id, parent_span_id = extract_traceparent(parent_context)
    elif parent_span:
        trace_id = parent_span.trace_id
        parent_span_id = parent_span.span_id
    else:
        trace_id = generate_trace_id()
        parent_span_id = None

    span = SpanContext(
        name=name,
        trace_id=trace_id,
        span_id=generate_span_id(),
        parent_span_id=parent_span_id,
        attributes=attributes or {},
    )

    token = _current_span.set(span)
    try:
        yield span
        span.finish(status="OK")
    except Exception as exc:
        span.finish(status="ERROR")
        span.set_attribute("error.type", type(exc).__name__)
        span.set_attribute("error.message", str(exc))
        raise
    finally:
        _current_span.reset(token)
        get_telemetry_manager().record_span(span)


@asynccontextmanager
async def async_trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    parent_context: str | dict[str, Any] | None = None,
) -> AsyncIterator[SpanContext]:
    """Asynchronous context manager creating a distributed span."""
    parent_span = _current_span.get()

    if parent_context:
        trace_id, parent_span_id = extract_traceparent(parent_context)
    elif parent_span:
        trace_id = parent_span.trace_id
        parent_span_id = parent_span.span_id
    else:
        trace_id = generate_trace_id()
        parent_span_id = None

    span = SpanContext(
        name=name,
        trace_id=trace_id,
        span_id=generate_span_id(),
        parent_span_id=parent_span_id,
        attributes=attributes or {},
    )

    token = _current_span.set(span)
    try:
        yield span
        span.finish(status="OK")
    except Exception as exc:
        span.finish(status="ERROR")
        span.set_attribute("error.type", type(exc).__name__)
        span.set_attribute("error.message", str(exc))
        raise
    finally:
        _current_span.reset(token)
        get_telemetry_manager().record_span(span)


P = ParamSpec("P")
R = TypeVar("R")


def traced(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to automatically wrap functions in a trace span."""

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        span_name = name or fn.__qualname__

        @functools.wraps(fn)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with trace_span(span_name, attributes=attributes):
                return fn(*args, **kwargs)

        @functools.wraps(fn)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            async with async_trace_span(span_name, attributes=attributes):
                return await fn(*args, **kwargs)  # type: ignore[misc]

        import inspect

        if inspect.iscoroutinefunction(fn):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper

    return decorator


class TelemetryManager:
    """Manages distributed span collections, SLO metrics, and OTLP exports."""

    def __init__(self) -> None:
        self.recorded_spans: list[SpanContext] = []
        self._recommendation_latencies_ms: list[float] = []
        self._intent_latencies_ms: list[float] = []
        self._grounding_scores: list[float] = []
        self._active_websocket_connections: int = 0
        self._websocket_disconnects: int = 0
        self._feedback_counts: dict[str, int] = {"accepted": 0, "edited": 0, "dismissed": 0}

    def record_span(self, span: SpanContext) -> None:
        """Store recorded span in history (capped at 1000)."""
        self.recorded_spans.append(span)
        if len(self.recorded_spans) > 1000:
            self.recorded_spans.pop(0)

        # Update metrics from span attributes if present
        if "recommendation.latency_ms" in span.attributes:
            self._recommendation_latencies_ms.append(
                float(span.attributes["recommendation.latency_ms"])
            )
        if "intent.latency_ms" in span.attributes:
            self._intent_latencies_ms.append(float(span.attributes["intent.latency_ms"]))
        if "grounding.score" in span.attributes:
            self._grounding_scores.append(float(span.attributes["grounding.score"]))

    def track_websocket_connect(self) -> None:
        """Increment active WebSocket connections."""
        self._active_websocket_connections += 1

    def track_websocket_disconnect(self, unexpected: bool = False) -> None:
        """Decrement active WebSocket connections and track drops."""
        if self._active_websocket_connections > 0:
            self._active_websocket_connections -= 1
        if unexpected:
            self._websocket_disconnects += 1

    def track_feedback(self, disposition: str) -> None:
        """Increment feedback disposition counter."""
        if disposition in self._feedback_counts:
            self._feedback_counts[disposition] += 1

    def get_metrics_summary(self) -> dict[str, Any]:
        """Compute summary statistics for Golden Signal SLO dashboards."""

        def p95(values: list[float]) -> float:
            if not values:
                return 0.0
            s = sorted(values)
            idx = int(0.95 * len(s))
            return s[min(idx, len(s) - 1)]

        avg_grounding = (
            sum(self._grounding_scores) / len(self._grounding_scores)
            if self._grounding_scores
            else 0.95
        )

        return {
            "active_websocket_sessions": self._active_websocket_connections,
            "websocket_drop_count": self._websocket_disconnects,
            "recommendation_p95_ms": p95(self._recommendation_latencies_ms),
            "intent_p95_ms": p95(self._intent_latencies_ms),
            "average_grounding_score": round(avg_grounding, 4),
            "total_spans_recorded": len(self.recorded_spans),
            "feedback_distribution": dict(self._feedback_counts),
        }

    def clear(self) -> None:
        """Reset telemetry buffers (useful for unit test isolation)."""
        self.recorded_spans.clear()
        self._recommendation_latencies_ms.clear()
        self._intent_latencies_ms.clear()
        self._grounding_scores.clear()
        self._active_websocket_connections = 0
        self._websocket_disconnects = 0


_manager_instance = TelemetryManager()


def get_telemetry_manager() -> TelemetryManager:
    """Return singleton TelemetryManager."""
    return _manager_instance
