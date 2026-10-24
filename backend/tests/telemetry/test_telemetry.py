"""Unit Tests for Distributed OpenTelemetry Tracing & SLO Metrics (Phase P9.1, P9.8)."""

from __future__ import annotations

import pytest

from app.core.telemetry import (
    async_trace_span,
    extract_traceparent,
    generate_span_id,
    generate_trace_id,
    get_telemetry_manager,
    inject_traceparent,
    trace_span,
    traced,
)


@pytest.fixture(autouse=True)
def reset_telemetry() -> None:
    """Ensure clean telemetry state for each test."""
    manager = get_telemetry_manager()
    manager.clear()


def test_w3c_id_generation() -> None:
    """Verify trace_id is 32-hex and span_id is 16-hex characters."""
    trace_id = generate_trace_id()
    span_id = generate_span_id()

    assert len(trace_id) == 32
    assert int(trace_id, 16) >= 0
    assert len(span_id) == 16
    assert int(span_id, 16) >= 0


def test_extract_and_inject_traceparent() -> None:
    """Verify W3C traceparent extraction and injection."""
    valid_header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    trace_id, parent_id = extract_traceparent(valid_header)

    assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parent_id == "00f067aa0ba902b7"

    # From carrier dict
    carrier = {"traceparent": valid_header}
    t_id, p_id = extract_traceparent(carrier)
    assert t_id == trace_id
    assert p_id == parent_id

    # Malformed carrier generates fresh trace_id
    bad_t_id, bad_p_id = extract_traceparent("invalid-traceparent-format")
    assert len(bad_t_id) == 32
    assert bad_p_id is None

    # Injection
    out_carrier: dict[str, str] = {}
    inject_traceparent(out_carrier, trace_id=trace_id, span_id=parent_id)
    assert out_carrier["traceparent"] == valid_header


def test_synchronous_nested_trace_spans() -> None:
    """Verify nested synchronous spans maintain trace_id and link parent_span_id."""
    with trace_span("parent_operation", attributes={"env": "test"}) as parent:
        assert parent.name == "parent_operation"
        assert parent.parent_span_id is None

        with trace_span("child_operation") as child:
            assert child.trace_id == parent.trace_id
            assert child.parent_span_id == parent.span_id
            child.set_attribute("chunk_count", 5)
            child.add_event("chunks_retrieved", {"count": 5})

        assert child.duration_ms >= 0.0
        assert child.status == "OK"

    assert parent.duration_ms >= 0.0
    assert parent.status == "OK"

    manager = get_telemetry_manager()
    assert len(manager.recorded_spans) == 2


@pytest.mark.asyncio
async def test_asynchronous_trace_spans() -> None:
    """Verify async_trace_span works correctly in async coroutines."""
    async with async_trace_span("async_orchestration") as span:
        span.set_attribute("async", True)
        assert span.status == "OK"

    assert span.end_time_ns is not None
    assert span.duration_ms >= 0.0


def test_traced_decorator_sync_and_async() -> None:
    """Verify @traced decorator instruments both sync and async functions."""

    @traced("decorated_sync")
    def sync_calc(a: int, b: int) -> int:
        return a + b

    @traced("decorated_async")
    async def async_calc(x: int) -> int:
        return x * 2

    import asyncio

    res_sync = sync_calc(2, 3)
    res_async = asyncio.run(async_calc(5))

    assert res_sync == 5
    assert res_async == 10

    manager = get_telemetry_manager()
    span_names = [s.name for s in manager.recorded_spans]
    assert "decorated_sync" in span_names
    assert "decorated_async" in span_names


def test_telemetry_manager_slo_metrics() -> None:
    """Verify TelemetryManager computes p95 latency and tracks connection events."""
    manager = get_telemetry_manager()

    # Track WebSockets
    manager.track_websocket_connect()
    manager.track_websocket_connect()
    assert manager.get_metrics_summary()["active_websocket_sessions"] == 2

    manager.track_websocket_disconnect(unexpected=True)
    assert manager.get_metrics_summary()["active_websocket_sessions"] == 1
    assert manager.get_metrics_summary()["websocket_drop_count"] == 1

    # Record synthetic recommendation spans with latencies
    with trace_span(
        "rec1", attributes={"recommendation.latency_ms": 100.0, "grounding.score": 0.95}
    ):
        pass
    with trace_span(
        "rec2", attributes={"recommendation.latency_ms": 200.0, "grounding.score": 0.98}
    ):
        pass
    with trace_span(
        "rec3", attributes={"recommendation.latency_ms": 500.0, "grounding.score": 0.92}
    ):
        pass

    summary = manager.get_metrics_summary()
    assert summary["recommendation_p95_ms"] > 0
    assert summary["average_grounding_score"] == pytest.approx(0.95, rel=1e-2)
    assert summary["total_spans_recorded"] == 3


@pytest.mark.asyncio
async def test_feedback_api_submission_and_telemetry() -> None:
    """Verify submit_feedback router function records feedback disposition and returns valid response."""
    from app.api.feedback import AgentFeedbackRequest, submit_feedback

    payload = AgentFeedbackRequest(
        session_id="test_session_456",
        item_type="recommendation",
        item_id="rec_123",
        agent_disposition="accepted",
        rating=1,
        comment="Accurate card replacement procedure suggestion.",
    )

    response = await submit_feedback(payload)
    assert response["status"] == "success"
    assert response["agent_disposition"] == "accepted"
    assert response["session_id"] == "test_session_456"

    # Verify telemetry disposition counter incremented
    manager = get_telemetry_manager()
    summary = manager.get_metrics_summary()
    assert summary["feedback_distribution"]["accepted"] >= 1


def test_feedback_api_validation_error() -> None:
    """Verify invalid feedback submission raises Pydantic ValidationError."""
    from pydantic import ValidationError

    from app.api.feedback import AgentFeedbackRequest

    with pytest.raises(ValidationError):
        AgentFeedbackRequest(
            session_id="test_session",
            item_type="invalid_item_type",  # type: ignore[arg-type]
            item_id="item_1",
            agent_disposition="unknown",  # type: ignore[arg-type]
        )


def test_metrics_summary_structure() -> None:
    """Verify TelemetryManager summary matches expected Golden Signal keys."""
    manager = get_telemetry_manager()
    summary = manager.get_metrics_summary()

    assert "active_websocket_sessions" in summary
    assert "websocket_drop_count" in summary
    assert "recommendation_p95_ms" in summary
    assert "intent_p95_ms" in summary
    assert "average_grounding_score" in summary
    assert "total_spans_recorded" in summary
    assert "feedback_distribution" in summary
