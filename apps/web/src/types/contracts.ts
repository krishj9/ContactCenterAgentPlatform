/**
 * Versioned WebSocket Event Contracts (v1) for Frontend TypeScript Client.
 *
 * Generated and strictly aligned with backend/app/contracts/events_v1.py.
 */

export type EventRole = 'customer' | 'agent' | 'system';

export type GroundingStatus =
  | 'GROUNDED'
  | 'POLICY_REVIEW_NEEDED'
  | 'MISSING_EVIDENCE'
  | 'UNGROUNDED';

export type GuardrailSeverity = 'INFO' | 'WARNING' | 'ERROR';

export type ActionType = 'GUIDANCE' | 'PROCEDURAL' | 'COMPLIANCE' | 'ESCALATION';

export interface ProvenancePayload {
  model_version: string;
  taxonomy_version: string;
  corpus_version: string;
  prompt_version: string;
}

export interface CustomerContextPayload {
  customer_id: string;
  name: string;
  account_type: string;
  relationship_tier: string;
  account_number_masked: string;
  context_summary: string;
  extra?: Record<string, unknown>;
}

export interface IntentCandidatePayload {
  intent_label: string;
  confidence: number;
}

export interface EvidenceItemPayload {
  chunk_id: string;
  store_type: 'policy' | 'faq';
  title: string;
  snippet: string;
  similarity_score: number;
  source_uri?: string | null;
  risk_level?: string | null;
}

export interface NextBestActionPayload {
  action_id: string;
  title: string;
  description: string;
  action_type: ActionType;
  steps: string[];
  is_grounded: boolean;
  grounding_state: GroundingStatus;
  citations: string[];
}

export interface SuggestedResponsePayload {
  response_id: string;
  text: string;
  rationale: string;
  is_editable: boolean;
  grounding_state: GroundingStatus;
  citations: string[];
}

// ----------------------------------------------------------------------------
// Inbound Events (Client -> Server)
// ----------------------------------------------------------------------------

export interface BaseEvent {
  event_id: string;
  timestamp: string;
}

export interface SessionJoinEvent extends BaseEvent {
  type: 'session.join';
  session_id: string;
  participant_id: string;
  role: EventRole;
  auth_token?: string | null;
}

export interface AudioChunkEvent extends BaseEvent {
  type: 'audio.chunk';
  session_id: string;
  participant_id: string;
  role: EventRole;
  seq: number;
  sample_rate: number;
  channels: number;
  format: string;
  payload_base64?: string | null;
}

export interface TranscriptManualEvent extends BaseEvent {
  type: 'transcript.manual';
  session_id: string;
  speaker: EventRole;
  text: string;
}

export interface SessionEndEvent extends BaseEvent {
  type: 'session.end';
  session_id: string;
  reason: string;
}

export type InboundEvent =
  | SessionJoinEvent
  | AudioChunkEvent
  | TranscriptManualEvent
  | SessionEndEvent;

// ----------------------------------------------------------------------------
// Outbound Events (Server -> Client)
// ----------------------------------------------------------------------------

export interface SessionReadyEvent extends BaseEvent {
  type: 'session.ready';
  session_id: string;
  participant_id: string;
  role: EventRole;
  status: string;
  customer_context?: CustomerContextPayload | null;
}

export interface TranscriptPartialEvent extends BaseEvent {
  type: 'transcript.partial';
  session_id: string;
  turn_id: number;
  speaker: EventRole;
  text: string;
  is_final: false;
}

export interface TranscriptFinalEvent extends BaseEvent {
  type: 'transcript.final';
  session_id: string;
  turn_id: number;
  speaker: EventRole;
  text: string;
  is_final: true;
  duration_ms: number;
}

export interface IssueUpdateEvent extends BaseEvent {
  type: 'issue.update';
  session_id: string;
  turn_id: number;
  intent_label: string;
  confidence: number;
  is_out_of_scope: boolean;
  candidates: IntentCandidatePayload[];
  exemplar_ids: string[];
  provenance: ProvenancePayload;
}

export interface AssistRecommendationEvent extends BaseEvent {
  type: 'assist.recommendation';
  session_id: string;
  turn_id: number;
  recommendations: NextBestActionPayload[];
  suggested_response?: SuggestedResponsePayload | null;
  evidence: EvidenceItemPayload[];
  grounding_state: GroundingStatus;
  provenance: ProvenancePayload;
}

export interface GuardrailAlertEvent extends BaseEvent {
  type: 'guardrail.alert';
  session_id: string;
  turn_id?: number | null;
  code: string;
  message: string;
  severity: GuardrailSeverity;
}

export interface SummaryReadyEvent extends BaseEvent {
  type: 'summary.ready';
  session_id: string;
  call_overview: string;
  key_issues: string[];
  actions_completed: string[];
  required_followups: string[];
  crm_case_note: string;
  provenance: ProvenancePayload;
}

export type OutboundEvent =
  | SessionReadyEvent
  | TranscriptPartialEvent
  | TranscriptFinalEvent
  | IssueUpdateEvent
  | AssistRecommendationEvent
  | GuardrailAlertEvent
  | SummaryReadyEvent;

export type WebSocketEvent = InboundEvent | OutboundEvent;
