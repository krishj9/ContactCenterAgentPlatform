# ADR-006: Human-in-the-Loop Assist Invariant (Strict Rule R14)

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board & Compliance
* **Context**: Technical Specification §1.2, Strict Invariant R14

---

## Context & Problem Statement
In retail and commercial banking contact centers, automated agent actions (e.g., waiving late fees, removing debit card holds, modifying travel itineraries) carry regulatory liabilities (Regulation E, CFPB guidelines) and fraud risks. If an autonomous GenAI model makes incorrect automated decisions or auto-executes financial transactions, the financial institution faces non-compliance penalties and customer financial losses.

## Decision
We established a strict, unviolable architectural invariant: **The platform is strictly assistive and shall NEVER autonomously execute operational banking actions.**
1. **Editable Suggestions**: All generated responses are presented in the Agent Cockpit as draft suggestions that the human agent must explicitly review, edit, copy, or speak.
2. **Manual Action Execution**: Next-best action cards provide step-by-step checklists and procedural instructions; the platform does not execute core banking API calls automatically.
3. **No Auto-Speaking**: The system does not synthesize voice audio directly back to the customer on the voice channel.
4. **Agent Feedback Loop**: Agents evaluate every recommendation (Apply, Modify, Dismiss), streaming telemetry back to the retraining pipeline.

## Consequences

### Positive
* **100% Regulatory Compliance**: Zero risk of rogue AI transactions or unauthorized fund movements.
* **Continuous Feedback Data**: Human modifications generate high-quality supervised preference data for model fine-tuning.

### Negative / Trade-offs
* Full resolution time relies on human agent speed; does not replace human contact center agents.
