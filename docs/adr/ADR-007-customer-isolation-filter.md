# ADR-007: Outbound Event Customer Isolation Filter (Strict Rule R9)

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board & Security
* **Context**: Technical Specification §3.1, Strict Invariant R9

---

## Context & Problem Statement
In a shared session, both the customer and the human agent connect to the backend WebSocket gateway. The backend generates internal assist events (`issue.update`, `assist.recommendation`, `response_suggestion.update`, `guardrail.warning`, `evidence.drawer`) intended solely for the agent. If an internal assist event is inadvertently broadcast to a customer WebSocket connection, the customer could view proprietary internal fraud rules, policy checklists, or internal system notes.

## Decision
We implemented a **cryptographically enforced Outbound Event Filter** in the session broadcast layer (`app.security.outbound_filter` and `SessionConnectionManager`):
1. **Role-Based Token Verification**: The gateway verifies the signed JWT join token and assigns the connection role (`Role.CUSTOMER` or `Role.AGENT`).
2. **Whitelist Invariant**: Connections with `role == CUSTOMER` are strictly permitted to receive only public conversation events:
   * `session.ready` (with masked customer profile only)
   * `transcript.final`
   * `transcript.partial`
   * `session.end`
3. **Hardware & CI Tests**: Any attempt to dispatch an assist event to a customer connection is blocked at the transport layer and raises an assertion error in CI (`test_outbound_event_filter_customer_isolation`).

## Consequences

### Positive
* **Zero Internal Data Leakage**: Customers can never inspect internal fraud policies, confidence scores, or assist metadata in browser developer tools or network logs.
* **Separation of Concerns**: The customer view remains a clean, focused voice and chat interface.

### Negative / Trade-offs
* Requires strict participant role tracking in the connection manager.
