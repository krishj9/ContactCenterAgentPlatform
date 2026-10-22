/**
 * Zustand Store Contract Interfaces.
 *
 * Defines contract interfaces for state management stores used across
 * the Agent Cockpit and Customer views.
 */

import type {
  CustomerContextPayload,
  EventRole,
  EvidenceItemPayload,
  GroundingStatus,
  GuardrailAlertEvent,
  IssueUpdateEvent,
  NextBestActionPayload,
  SuggestedResponsePayload,
  SummaryReadyEvent,
} from '../types/contracts';

// ----------------------------------------------------------------------------
// Session Store Interface
// ----------------------------------------------------------------------------

export type ConnectionState = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';

export interface SessionStoreState {
  sessionId: string | null;
  participantId: string | null;
  role: EventRole | null;
  connectionState: ConnectionState;
  customerContext: CustomerContextPayload | null;
  error: string | null;

  // Actions
  setConnectionState: (state: ConnectionState) => void;
  setSession: (sessionId: string, participantId: string, role: EventRole) => void;
  setCustomerContext: (context: CustomerContextPayload) => void;
  setError: (error: string | null) => void;
  resetSession: () => void;
}

// ----------------------------------------------------------------------------
// Transcript Store Interface
// ----------------------------------------------------------------------------

export interface TranscriptTurnItem {
  turn_id: number;
  speaker: EventRole;
  text: string;
  is_final: boolean;
  timestamp: string;
  duration_ms?: number;
}

export interface TranscriptStoreState {
  turns: TranscriptTurnItem[];
  partialCustomerText: string;
  partialAgentText: string;

  // Actions
  appendPartialText: (speaker: EventRole, text: string) => void;
  finalizeTurn: (turn: TranscriptTurnItem) => void;
  clearTranscript: () => void;
}

// ----------------------------------------------------------------------------
// Assist Store Interface
// ----------------------------------------------------------------------------

export interface AssistStoreState {
  currentTurnId: number | null;
  intentLabel: string | null;
  intentConfidence: number;
  isOutOfScope: boolean;
  exemplarIds: string[];
  recommendations: NextBestActionPayload[];
  suggestedResponse: SuggestedResponsePayload | null;
  evidence: EvidenceItemPayload[];
  groundingState: GroundingStatus;
  guardrailAlerts: GuardrailAlertEvent[];
  summary: SummaryReadyEvent | null;

  // Actions
  handleIssueUpdate: (event: IssueUpdateEvent) => void;
  handleAssistRecommendation: (
    recommendations: NextBestActionPayload[],
    suggestedResponse?: SuggestedResponsePayload | null,
    evidence?: EvidenceItemPayload[],
    groundingState?: GroundingStatus
  ) => void;
  handleGuardrailAlert: (alert: GuardrailAlertEvent) => void;
  handleSummaryReady: (summary: SummaryReadyEvent) => void;
  clearAssist: () => void;
}

// ----------------------------------------------------------------------------
// Audio Store Interface
// ----------------------------------------------------------------------------

export interface AudioStoreState {
  isCapturing: boolean;
  isMuted: boolean;
  audioLevel: number;
  sampleRate: number;
  packetsSent: number;

  // Actions
  startCapture: () => Promise<void>;
  stopCapture: () => void;
  setMuted: (muted: boolean) => void;
  setAudioLevel: (level: number) => void;
  incrementPackets: () => void;
  resetAudio: () => void;
}
