# Browser Voice Agent Helper (Banking POC) — Requirements

## 0. Purpose

Build a browser-based AI Agent Helper for banking-style customer support where a customer and a human agent join the same live voice session from their browsers, and the agent receives real-time assist features such as transcript, issue hints, grounded next-best actions, suggested responses, and post-call summary artifacts. [file:575]

This is a demo-oriented, synthetic-data-only application. The agent always remains in control; the system must never auto-speak, auto-send, or auto-execute customer-facing actions. [file:575]

## 1. Product goals

The application must:
- Support one customer and one agent in a shared browser-based voice session.
- Produce live partial and final transcripts with speaker attribution.
- Show agent-assist outputs during the call.
- Ground operational guidance using evidence from retrieval stores.
- Generate a structured post-call summary and wrap-up note.
- Run locally for development without requiring telephony platforms. [file:575]

## 2. Scope

### In scope
- Single-session browser voice conversation between one customer and one agent.
- Browser microphone capture and streaming audio to a backend.
- Streaming speech-to-text with partial and final transcript updates.
- Real-time issue or intent detection from transcript.
- Retrieval from logical stores:
  - Intent store for utterance examples and issue support.
  - Policy store for operational and compliance guidance.
  - FAQ store for customer-facing explanatory content.
- Grounded next-best-action cards.
- Suggested response drafts for the agent.
- Evidence visibility for grounded outputs.
- Guardrails for low confidence, missing evidence, and policy conflict.
- End-of-call summary and case note draft.
- Audit logging of key system events.
- Synthetic customer profiles, scripted scenarios, and synthetic corpora only. [file:575]

### Out of scope
- Amazon Connect, Twilio, PSTN, SIP, IVR, ACD queues, and telephony provisioning.
- Multi-party sessions beyond one customer and one agent.
- Production-grade compliance retention, workforce management, and enterprise contact-center operations.
- Real customer data or live banking systems.
- Autonomous action execution such as fee reversal, card unblocking, or outbound communication. [file:575]

## 3. Users and roles

### Customer
- Joins a voice session from a browser.
- Speaks naturally with the human agent.
- Does not see internal recommendations, evidence, or guardrail states.

### Agent
- Joins the same session from a browser.
- Sees live transcript, synthetic customer context, issue hints, grounded recommendations, evidence, guardrail warnings, and post-call summary.
- Decides what to say and what actions to take.

### System
- Manages session state, audio ingestion, transcript generation, retrieval, grounding, recommendation generation, summary generation, and audit logging. [file:575][file:576]

## 4. Assumptions

- The application is a POC and should prefer deterministic, testable behavior over high-complexity autonomy.
- Synthetic scenarios and synthetic customer data will be used throughout development and demos.
- The first local development target should run with minimal external dependencies where possible.
- Retrieval-backed action guidance requires a dedicated policy corpus; this corpus must be authored or curated explicitly as part of the build plan.
- LLM-assisted generation is allowed for recommendations and summaries, but the system must support a rules-first fallback where practical. [file:575][file:576][file:577]

## 5. Functional requirements

### R1. Session creation and joining
WHEN an agent starts a demo session,
THE SYSTEM SHALL create a session and return join information for both customer and agent participants.

Acceptance criteria:
- A session can be created using an HTTP API.
- Customer and agent can join using a session ID or join token.
- Session state is visible as created, active, ended, or failed.
- Invalid or expired join attempts are rejected cleanly.

### R2. Browser voice session
WHEN the customer and agent are connected,
THE SYSTEM SHALL allow them to participate in the same browser-based voice session.

Acceptance criteria:
- Browser microphone permission is requested explicitly.
- The UI shows connection state, microphone state, and in-call state.
- Reconnect behavior is defined for temporary disconnects.

### R3. Audio streaming
WHEN a participant speaks,
THE SYSTEM SHALL stream audio chunks from the browser to the backend in near real time.

Acceptance criteria:
- Audio chunks are sequence-numbered or otherwise ordered.
- The backend can associate audio with a session and participant role.
- The system handles temporary packet loss or dropped chunks without crashing the session.

### R4. Streaming transcription
WHEN audio is streamed,
THE SYSTEM SHALL produce partial and final transcript events labeled with the correct speaker.

Acceptance criteria:
- Partial transcript appears while speech is in progress.
- Final transcript supersedes the relevant partial segment.
- Transcript ordering is preserved by session and event sequence.
- Transcript events include timestamps and speaker role.

### R5. Agent transcript view
WHEN the session is active,
THE SYSTEM SHALL display a rolling transcript for the agent.

Acceptance criteria:
- Transcript updates without page refresh.
- Customer and agent turns are visually distinguishable.
- Recent turns remain visible in time order.
- Partial and final transcript states are visually differentiated.

### R6. Customer context panel
WHEN the agent joins a session,
THE SYSTEM SHALL display a synthetic customer profile relevant to the scenario.

Acceptance criteria:
- Display synthetic customer name, account type, relationship tier, and scenario context.
- The customer context is retrieved from scenario fixtures or a CRM-like service.
- No real PII is used.

### R7. Issue or intent detection
WHEN customer speech contains a banking issue,
THE SYSTEM SHALL infer one or more likely issue hypotheses from the transcript.

Acceptance criteria:
- The system publishes issue labels with confidence scores.
- The top issue should match the expected scenario label in scripted demos.
- The system may return multiple issues if the conversation is ambiguous.

### R8. Logical retrieval stores
WHEN the system requires supporting context,
THE SYSTEM SHALL retrieve from separate logical stores for intent, policy, and FAQ content.

Acceptance criteria:
- Each record has a stable ID and metadata.
- Each store can be queried independently.
- A query can target one or more stores.
- Store-specific metadata is preserved in retrieval results.

### R9. Retrieval routing
WHEN retrieval is triggered,
THE SYSTEM SHALL route queries to appropriate stores based on use case.

Acceptance criteria:
- Intent store supports issue inference and utterance matching.
- Policy store is required before presenting operational guidance as grounded.
- FAQ store supports customer-facing explanation language.
- Retrieval routing is testable and configurable.

### R10. Grounded next-best actions
WHEN enough evidence is available,
THE SYSTEM SHALL generate grounded next-best-action cards for the agent.

Acceptance criteria:
- Each card contains title, body, confidence, state, and sources.
- Operational actions are not marked grounded without policy support.
- The system may suppress an action instead of generating an unsupported one.

### R11. Suggested responses
WHEN a recommendation or explanation is useful,
THE SYSTEM SHALL generate an editable suggested-response draft for the agent.

Acceptance criteria:
- The suggestion is phrased as if spoken by the agent.
- The suggestion is editable by the agent.
- The system never auto-sends or auto-speaks the suggestion.

### R12. Evidence visibility
WHEN a recommendation or suggestion is shown,
THE SYSTEM SHALL show its supporting evidence when available.

Acceptance criteria:
- Evidence includes source type, source ID, title, and snippet.
- Agent UI can reveal the evidence associated with a recommendation.
- Grounded outputs always include at least one evidence item.

### R13. Guardrails and safety
WHEN evidence is weak, missing, or conflicting,
THE SYSTEM SHALL downgrade, warn, or suppress outputs.

Acceptance criteria:
- Supported states include grounded, low_confidence, missing_evidence, and policy_review_needed.
- Policy conflict is surfaced as a warning.
- Unsupported outputs are never mislabeled as grounded.

### R14. No autonomous action
WHEN any assistive output is generated,
THE SYSTEM SHALL preserve human-in-the-loop control.

Acceptance criteria:
- No backend or frontend path automatically sends customer-facing text.
- No code path automatically performs an operational banking action.
- Assistive outputs are clearly presented as suggestions.

### R15. End-of-call summary
WHEN the session ends,
THE SYSTEM SHALL generate a structured summary and case note draft.

Acceptance criteria:
- Summary includes overview, issues discussed, actions discussed, unresolved items, and case note draft.
- Summary is persisted and retrievable after the call.
- Summary reflects the transcript and session state for scripted scenarios.

### R16. Audit logging
WHEN key events occur,
THE SYSTEM SHALL record audit events.

Acceptance criteria:
- Log session lifecycle events.
- Log transcript segment creation or references.
- Log retrieval calls and target stores.
- Log recommendation states and IDs.
- Log summary generation and user disposition actions where applicable.

### R17. Scripted scenarios and replay
WHEN the application is used for demos or evaluation,
THE SYSTEM SHALL support scripted scenarios and transcript replay.

Acceptance criteria:
- Scenario fixtures exist for at least card declined, fee dispute, and travel notice.
- Transcript replay can feed the system without live audio.
- Replay outputs can be captured for regression testing.

## 6. Non-functional requirements

### NFR1. Live responsiveness
- Partial transcript should appear quickly enough to feel live in normal demo conditions.
- Final transcript should arrive promptly after speech completion.
- Retrieval and recommendation updates should not block transcript flow.

### NFR2. Local-first development
- The application must be runnable locally with documented setup steps.
- A local development mode should exist without requiring telephony platforms.
- Local storage and local vector backends should be supported.

### NFR3. Safety bias
- The system must prefer no recommendation over ungrounded guidance.
- Missing policy support must reduce or suppress operational recommendations.

### NFR4. Modularity
- Frontend, session gateway, transcription, retrieval, grounding, recommendation, and summary modules should remain separable.

### NFR5. Deterministic contracts
- REST and WebSocket event schemas must be explicit and versionable.
- Structured outputs from LLM-dependent components must be validated before use.

### NFR6. Synthetic data only
- No real customer data, no production banking systems, and no real account identifiers may be used.

### NFR7. Testability
- Core logic must be testable without live STT, live vector DB access, or live cloud models.
- Mock-driven unit and integration tests must cover major flows.

## 7. Data and corpus requirements

The system requires three logical corpora:

### Intent corpus
- Banking issue utterances and intent examples.
- Used for issue detection support and similarity matching.

### FAQ corpus
- Customer-friendly explanatory content.
- Used to support suggested responses and explanatory language.

### Policy corpus
- Curated operational and compliance guidance for the POC.
- Used to support or suppress action-oriented recommendations.
- Must be authored or curated explicitly; this corpus cannot be assumed to exist implicitly.

Each normalized record should include:
- record_id
- store_type
- title
- text or chunk_text
- source_name
- source_reference
- scenario_tags
- metadata
- version [file:575][file:576][file:577]

## 8. Environment profiles

The system should support these execution profiles:

- Local demo profile: SQLite + local vector backend + mocked or configurable STT/LLM providers.
- Cloud-assisted profile: FastAPI + cloud embeddings/model provider + Pinecone or equivalent vector store.
- Replay/evaluation profile: no live audio, transcript-driven execution path. [file:576][file:577]

## 9. Open decisions

The implementation must explicitly resolve:
- STT provider for local and cloud modes.
- Recommendation generation mode: rules-first only, LLM-assisted, or hybrid.
- Summary generation mode: rules-first, LLM-assisted, or hybrid.
- Default vector backend for local development.
- Final source and format of the policy corpus. [file:576][file:577]