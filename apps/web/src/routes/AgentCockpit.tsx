/**
 * Agent Cockpit UI Assembly (/agent).
 *
 * Full 3-column desktop layout integrating:
 * - Col 1: CustomerContextPanel (synthetic CRM history, authentication status, balances)
 * - Col 2: TranscriptTimeline (virtualized feed, partial styling, keyword search) & input controls
 * - Col 3: IntentChip, GroundingBanner, NextBestActionCard, SuggestedResponseCard
 * - Drawers: EvidenceDrawer, SummaryModal
 */

import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Mic,
  MicOff,
  Send,
  PhoneOff,
  Clock,
  FileText,
  Layers,
  Sparkles,
} from "lucide-react";

import { CustomerContextPanel } from "@/components/agent/CustomerContextPanel";
import { TranscriptTimeline, type TimelineTurn } from "@/components/agent/TranscriptTimeline";
import { IntentChip } from "@/components/agent/IntentChip";
import { GroundingBanner } from "@/components/agent/GroundingBanner";
import { NextBestActionCard, type ActionStepItem } from "@/components/agent/NextBestActionCard";
import { SuggestedResponseCard } from "@/components/agent/SuggestedResponseCard";
import { EvidenceDrawer } from "@/components/agent/EvidenceDrawer";
import { SummaryModal } from "@/components/agent/SummaryModal";

import { useAudioWorklet } from "@/audio/useAudioWorklet";
import { WebSocketClient, type ConnectionState } from "@/services/websocket";
import type {
  IntentCandidatePayload,
  GroundingStatus,
  EvidenceItemPayload,
  TranscriptPartialEvent,
  TranscriptFinalEvent,
  AssistRecommendationEvent,
  IssueUpdateEvent,
} from "@/types/contracts";

export default function AgentCockpit() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get("session_id") || "sess_card_declined_101";

  // Telemetry & Timers
  const [callDuration, setCallDuration] = useState(128); // seconds
  const [inputText, setInputText] = useState("");
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");

  // Modals & Drawers
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState(false);
  const [selectedCitationId, setSelectedCitationId] = useState<string | null>(null);
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);

  // Real-time Intent & Grounding State (P4, P5)
  const [activeIntent, setActiveIntent] = useState("card_declined");
  const [activeConfidence, setActiveConfidence] = useState(0.942);
  const [isOutOfScope, setIsOutOfScope] = useState(false);
  const [isDegraded, setIsDegraded] = useState(false);
  const [intentCandidates, setIntentCandidates] = useState<IntentCandidatePayload[]>([
    { intent_label: "card_declined", confidence: 0.942 },
    { intent_label: "country_support", confidence: 0.038 },
    { intent_label: "general_inquiry", confidence: 0.02 },
  ]);
  const [exemplarIds, setExemplarIds] = useState<string[]>([
    "ex-card_declined-1",
    "ex-card_declined-2",
    "ex-card_declined-3",
  ]);
  const [lastCustomerUtterance, setLastCustomerUtterance] = useState(
    "Hi Alex, I'm currently in France and my Sapphire card was just declined at a restaurant in Paris. I need to pay the bill right now."
  );

  const [groundingState, setGroundingState] = useState<GroundingStatus>("GROUNDED");
  const [warningMessage, setWarningMessage] = useState<string | null>(null);
  const [nbaTitle, setNbaTitle] = useState("Lift Geographic Decline & Register Travel Notice");
  const [nbaDescription, setNbaDescription] = useState(
    "Card declined overseas due to unexpected geo-location. Verify cardholder presence and apply temporary 24h override."
  );
  const [nbaActionType, setNbaActionType] = useState<"verify" | "inform" | "escalate">("verify");
  const [nbaSteps, setNbaSteps] = useState<ActionStepItem[]>([
    {
      id: "step-1",
      step_number: 1,
      text: "Verify cardholder identity and confirm merchant POS terminal location in Paris, France.",
      action_type: "verify",
      citation_ids: ["pol_card_decline_01_s4_c1"],
    },
    {
      id: "step-2",
      step_number: 2,
      text: "Lift temporary 24h geographic decline rule for card ending in 4821.",
      action_type: "inform",
      citation_ids: ["pol_card_decline_01_s4_c1"],
    },
    {
      id: "step-3",
      step_number: 3,
      text: "Register 30-day travel authorization for France and Schengen region to prevent recurring blocks.",
      action_type: "inform",
      citation_ids: ["pol_travel_notice_03_s2_c1"],
    },
  ]);
  const [nbaCitations, setNbaCitations] = useState<string[]>([
    "pol_card_decline_01_s4_c1",
    "pol_travel_notice_03_s2_c1",
  ]);
  const [suggestedText, setSuggestedText] = useState(
    "I see the automated security trigger on your Sapphire card from a transaction in Paris, Sarah. I have verified your identity and can lift this geographic hold immediately so you can complete your payment."
  );
  const [suggestedRationale, setSuggestedRationale] = useState(
    "Acknowledge urgent dining POS decline, validate security presence, and confirm immediate override."
  );
  const [evidenceList, setEvidenceList] = useState<EvidenceItemPayload[]>([
    {
      chunk_id: "pol_card_decline_01_s4_c1",
      store_type: "policy",
      title: "Operational Policy: Card Authorization & Geographic Security Rules",
      snippet:
        "Section 4.1: Overseas POS Declines. When a cardholder contacts support regarding a real-time transaction decline abroad, the agent must authenticate Level 3 identity. Upon confirmation of cardholder presence, the agent is authorized to place a temporary 24-hour geographic decline override on terminal restrictions.",
      similarity_score: 0.892,
      source_uri: "policy/card_authorization_v2.pdf#section=4.1",
      risk_level: "LOW",
    },
    {
      chunk_id: "pol_travel_notice_03_s2_c1",
      store_type: "policy",
      title: "Operational Policy: Travel Notice Registration & Multi-Country Exemption",
      snippet:
        "Section 2.3: In-Flight Travel Notices. Agents may register travel notices retroactively during active international travel for up to 90 consecutive days. All Schengen area countries must be included when traveling within Western Europe.",
      similarity_score: 0.841,
      source_uri: "policy/travel_authorization_rules.pdf#section=2.3",
      risk_level: "LOW",
    },
    {
      chunk_id: "faq_card_declined_overseas_02",
      store_type: "faq",
      title: "Customer FAQ: Why was my credit card declined abroad?",
      snippet:
        "Unrecognized international charges trigger automated fraud algorithms to protect your balance. Support agents can immediately unlock foreign transaction permissions once verified.",
      similarity_score: 0.725,
      source_uri: "faq/international_transactions.md",
      risk_level: "LOW",
    },
  ]);

  // Dialogue turns
  const [turns, setTurns] = useState<TimelineTurn[]>([
    {
      id: "turn-1",
      turn_id: 1,
      speaker: "agent",
      text: "Hello, thank you for calling Premier Card Support. My name is Alex. How can I help you today?",
      time: "10:14:02",
      duration_ms: 3200,
    },
    {
      id: "turn-2",
      turn_id: 2,
      speaker: "customer",
      text: "Hi Alex, I'm currently in France and my Sapphire card was just declined at a restaurant in Paris. I need to pay the bill right now.",
      time: "10:14:18",
      duration_ms: 5400,
    },
    {
      id: "turn-3",
      turn_id: 3,
      speaker: "agent",
      text: "I completely understand how urgent this is while traveling abroad. Let me check your account security activity right away.",
      time: "10:14:35",
      duration_ms: 4100,
    },
  ]);
  const [partialCustomerText, setPartialCustomerText] = useState("");
  const [partialAgentText, setPartialAgentText] = useState("");

  const wsClientRef = useRef<WebSocketClient | null>(null);

  // Initialize WebSocket Client
  useEffect(() => {
    const client = new WebSocketClient({
      sessionId,
      role: "agent",
      participantId: "agent_alex_4029",
      autoConnect: true,
    });
    wsClientRef.current = client;

    const unsubState = client.onStateChange((st) => setConnectionState(st));

    const unsubPartial = client.on<TranscriptPartialEvent>("transcript.partial", (evt) => {
      if (evt.speaker === "customer") {
        setPartialCustomerText(evt.text);
      } else {
        setPartialAgentText(evt.text);
      }
    });

    const unsubFinal = client.on<TranscriptFinalEvent>("transcript.final", (evt) => {
      if (evt.speaker === "customer") {
        setPartialCustomerText("");
        setLastCustomerUtterance(evt.text);
      } else {
        setPartialAgentText("");
      }

      setTurns((prev) => [
        ...prev,
        {
          id: `turn_${evt.turn_id}_${Date.now()}`,
          turn_id: evt.turn_id,
          speaker: evt.speaker as "customer" | "agent",
          text: evt.text,
          time: new Date().toLocaleTimeString(),
          duration_ms: evt.duration_ms,
        },
      ]);
    });

    const unsubIssue = client.on<IssueUpdateEvent>("issue.update", (evt) => {
      setActiveIntent(evt.intent_label);
      setActiveConfidence(evt.confidence);
      setIsOutOfScope(evt.is_out_of_scope);
      if (evt.candidates) setIntentCandidates(evt.candidates);
      if (evt.exemplar_ids) setExemplarIds(evt.exemplar_ids);
    });

    const unsubAssist = client.on<AssistRecommendationEvent>("assist.recommendation", (evt) => {
      setGroundingState(evt.grounding_state);
      if (evt.recommendations && evt.recommendations.length > 0) {
        const topNba = evt.recommendations[0];
        setNbaTitle(topNba.title);
        setNbaDescription(topNba.description);
        setNbaSteps(
          topNba.steps.map((st, i) => ({
            id: `step-${i}`,
            step_number: i + 1,
            text: st,
            action_type: topNba.action_type.toLowerCase(),
            citation_ids: topNba.citations,
          }))
        );
        setNbaCitations(topNba.citations);
      }
      if (evt.suggested_response) {
        setSuggestedText(evt.suggested_response.text);
        setSuggestedRationale(evt.suggested_response.rationale);
      }
      if (evt.evidence) {
        setEvidenceList(evt.evidence);
      }
    });

    return () => {
      unsubState();
      unsubPartial();
      unsubFinal();
      unsubIssue();
      unsubAssist();
      client.disconnect();
    };
  }, [sessionId]);

  // AudioWorklet
  const { isRecording, audioLevel, startRecording, stopRecording } = useAudioWorklet({
    onAudioChunk: (pcmBuffer, seq) => {
      if (wsClientRef.current) {
        wsClientRef.current.sendAudioChunk(pcmBuffer, seq);
      }
    },
  });

  const toggleMic = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  // Call timer simulation
  useEffect(() => {
    const timer = setInterval(() => setCallDuration((d) => d + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDuration = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleSendManual = () => {
    if (!inputText.trim()) return;
    const text = inputText.trim();

    const newTurn: TimelineTurn = {
      id: `turn_${Date.now()}`,
      turn_id: turns.length + 1,
      speaker: "agent",
      text,
      time: new Date().toLocaleTimeString(),
      duration_ms: 0,
    };
    setTurns((prev) => [...prev, newTurn]);
    setInputText("");

    if (wsClientRef.current) {
      wsClientRef.current.send({
        type: "transcript.manual",
        event_id: `evt_${Date.now()}`,
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        speaker: "agent",
        text,
      });
    }
  };

  const handleCitationClick = (citationId: string) => {
    setSelectedCitationId(citationId);
    setIsEvidenceDrawerOpen(true);
  };

  const simulateScenario = (
    key: "card_declined" | "fee_dispute" | "policy_review" | "missing_evidence" | "out_of_scope" | "degraded"
  ) => {
    switch (key) {
      case "card_declined":
        setActiveIntent("card_declined");
        setActiveConfidence(0.942);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setGroundingState("GROUNDED");
        setWarningMessage(null);
        setIntentCandidates([
          { intent_label: "card_declined", confidence: 0.942 },
          { intent_label: "country_support", confidence: 0.038 },
          { intent_label: "general_inquiry", confidence: 0.02 },
        ]);
        setExemplarIds(["ex-card_declined-1", "ex-card_declined-2", "ex-card_declined-3"]);
        setLastCustomerUtterance("Hi Alex, I'm currently in France and my Sapphire card was just declined at a restaurant in Paris. I need to pay the bill right now.");
        setNbaTitle("Lift Geographic Decline & Register Travel Notice");
        setNbaDescription("Card declined overseas due to unexpected geo-location. Verify cardholder presence and apply temporary 24h override.");
        setNbaActionType("verify");
        setNbaSteps([
          {
            id: "step-1",
            step_number: 1,
            text: "Verify cardholder identity and confirm merchant POS terminal location in Paris, France.",
            action_type: "verify",
            citation_ids: ["pol_card_decline_01_s4_c1"],
          },
          {
            id: "step-2",
            step_number: 2,
            text: "Lift temporary 24h geographic decline rule for card ending in 4821.",
            action_type: "inform",
            citation_ids: ["pol_card_decline_01_s4_c1"],
          },
          {
            id: "step-3",
            step_number: 3,
            text: "Register 30-day travel authorization for France and Schengen region to prevent recurring blocks.",
            action_type: "inform",
            citation_ids: ["pol_travel_notice_03_s2_c1"],
          },
        ]);
        setNbaCitations(["pol_card_decline_01_s4_c1", "pol_travel_notice_03_s2_c1"]);
        setSuggestedText(
          "I see the automated security trigger on your Sapphire card from a transaction in Paris, Sarah. I have verified your identity and can lift this geographic hold immediately so you can complete your payment."
        );
        setSuggestedRationale("Acknowledge urgent dining POS decline, validate security presence, and confirm immediate override.");
        setEvidenceList([
          {
            chunk_id: "pol_card_decline_01_s4_c1",
            store_type: "policy",
            title: "Operational Policy: Card Authorization & Geographic Security Rules",
            snippet:
              "Section 4.1: Overseas POS Declines. When a cardholder contacts support regarding a real-time transaction decline abroad, the agent must authenticate Level 3 identity. Upon confirmation of cardholder presence, the agent is authorized to place a temporary 24-hour geographic decline override on terminal restrictions.",
            similarity_score: 0.892,
            source_uri: "policy/card_authorization_v2.pdf#section=4.1",
            risk_level: "LOW",
          },
          {
            chunk_id: "pol_travel_notice_03_s2_c1",
            store_type: "policy",
            title: "Operational Policy: Travel Notice Registration & Multi-Country Exemption",
            snippet:
              "Section 2.3: In-Flight Travel Notices. Agents may register travel notices retroactively during active international travel for up to 90 consecutive days. All Schengen area countries must be included when traveling within Western Europe.",
            similarity_score: 0.841,
            source_uri: "policy/travel_authorization_rules.pdf#section=2.3",
            risk_level: "LOW",
          },
        ]);
        break;

      case "fee_dispute":
        setActiveIntent("fee_dispute");
        setActiveConfidence(0.918);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setGroundingState("GROUNDED");
        setWarningMessage(null);
        setIntentCandidates([
          { intent_label: "fee_dispute", confidence: 0.918 },
          { intent_label: "card_payment_fee_charged", confidence: 0.052 },
          { intent_label: "general_inquiry", confidence: 0.03 },
        ]);
        setExemplarIds(["ex-fee_dispute-1", "ex-fee_dispute-2", "ex-fee_dispute-3"]);
        setLastCustomerUtterance("I noticed an overdraft fee of thirty-five dollars charged to my statement yesterday. Can this fee be waived?");
        setNbaTitle("Process Courtesy Fee Waiver ($35.00)");
        setNbaDescription("Account in good standing with 0 waivers in rolling 12 months. Apply one-time courtesy credit.");
        setNbaActionType("verify");
        setNbaSteps([
          {
            id: "step-1",
            step_number: 1,
            text: "Verify account has not received more than 2 courtesy waivers in past 12 rolling months.",
            action_type: "verify",
            citation_ids: ["pol_fee_dispute_02_s1_c1"],
          },
          {
            id: "step-2",
            step_number: 2,
            text: "Inform cardholder that the $35.00 overdraft fee is credited immediately to ledger.",
            action_type: "inform",
            citation_ids: ["pol_fee_dispute_02_s1_c1"],
          },
          {
            id: "step-3",
            step_number: 3,
            text: "If fee exceeds $50 or waiver limit reached, escalate to Account Resolution Supervisor.",
            action_type: "escalate",
            citation_ids: ["pol_fee_dispute_02_s3_c2"],
          },
        ]);
        setNbaCitations(["pol_fee_dispute_02_s1_c1", "pol_fee_dispute_02_s3_c2"]);
        setSuggestedText(
          "I reviewed your account history, Sarah. Because your account is in excellent standing and you haven't requested any fee waivers recently, I can gladly issue a one-time courtesy credit of $35.00 back to your card today."
        );
        setSuggestedRationale("Customer retention policy allows up to 2 courtesy refunds per year for Platinum tier.");
        setEvidenceList([
          {
            chunk_id: "pol_fee_dispute_02_s1_c1",
            store_type: "policy",
            title: "Operational Policy: Courtesy Fee Waiver Thresholds & Eligibility",
            snippet: "Platinum cardholders qualify for immediate frontline courtesy credits up to $50.00.",
            similarity_score: 0.875,
            source_uri: "policy/fee_waiver_guidelines.pdf",
            risk_level: "MEDIUM",
          },
        ]);
        break;

      case "policy_review":
        setActiveIntent("card_declined");
        setActiveConfidence(0.72);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setGroundingState("POLICY_REVIEW_NEEDED");
        setWarningMessage("Retrieved policy chunk score (0.58) below τ_policy (0.68). Operational unblock restricted.");
        setNbaTitle("Provide General Guidance (Policy Review Required)");
        setNbaDescription("Operational automated overrides are locked pending supervisor or direct policy confirmation.");
        setNbaActionType("inform");
        setNbaSteps([
          {
            id: "step-1",
            step_number: 1,
            text: "Explain that security protocols require secondary verification before manual card unblock.",
            action_type: "inform",
          },
          {
            id: "step-2",
            step_number: 2,
            text: "Verify customer contact details on file without executing account changes.",
            action_type: "verify",
          },
        ]);
        setNbaCitations([]);
        setSuggestedText(
          "I can see that the transaction wasn't authorized, Sarah. Because this requires additional security clearance, let me verify your contact information before having our risk desk assist."
        );
        break;

      case "missing_evidence":
        setActiveIntent("card_payment_not_recognised");
        setActiveConfidence(0.61);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setGroundingState("MISSING_EVIDENCE");
        setWarningMessage("No retrieved chunks exceeded the evidence threshold (τ_evidence = 0.48). Operational actions suppressed.");
        setNbaTitle("Record Dispute Details (Actions Suppressed)");
        setNbaDescription("Authoritative operational policies missing from local index. Recommendations restricted to intake.");
        setNbaActionType("inform");
        setNbaSteps([
          {
            id: "step-1",
            step_number: 1,
            text: "Listen to cardholder statement and record unrecognized charge details.",
            action_type: "inform",
          },
        ]);
        setNbaCitations([]);
        setSuggestedText(
          "I understand you don't recognize this charge on your statement, Sarah. I am documenting the merchant details now and will connect you with our fraud intake team."
        );
        setEvidenceList([]);
        break;

      case "out_of_scope":
        setActiveIntent("out_of_scope");
        setActiveConfidence(0.975);
        setIsOutOfScope(true);
        setIsDegraded(false);
        setGroundingState("LOW_CONFIDENCE");
        setWarningMessage("Query is out of scope. Automated procedural playbooks disabled.");
        setNbaTitle("Politely Redirect to Banking Services");
        setNbaDescription("Non-banking request detected. Assistive procedures suppressed.");
        setNbaActionType("inform");
        setNbaSteps([
          {
            id: "step-1",
            step_number: 1,
            text: "Politely clarify that agent assist is dedicated to card and account services.",
            action_type: "inform",
          },
        ]);
        setNbaCitations([]);
        setSuggestedText(
          "I specialize in cardholder support and account security, Sarah! While I don't have weather data, please let me know if you need any help with your Sapphire card or transactions."
        );
        setEvidenceList([]);
        break;

      case "degraded":
        setActiveIntent("card_declined");
        setActiveConfidence(0.88);
        setIsOutOfScope(false);
        setIsDegraded(true);
        setGroundingState("GROUNDED");
        setWarningMessage("Intent detected via k-NN fallback. Deterministic playbook engaged.");
        setNbaTitle("Playbook Fallback: Card Decline Routine");
        setNbaDescription("Synthesized from deterministic operational YAML playbook (R14 verified).");
        setNbaActionType("verify");
        setNbaSteps([
          {
            id: "step-1",
            step_number: 1,
            text: "Verify cardholder identity and confirm merchant POS terminal location.",
            action_type: "verify",
            citation_ids: ["pol_card_decline_01_s4_c1"],
          },
        ]);
        setNbaCitations(["pol_card_decline_01_s4_c1"]);
        setSuggestedText(
          "I see your card was declined at the terminal. I have confirmed your account security and can place a temporary override so you can retry the transaction immediately."
        );
        break;
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-blue-600/30 selection:text-white">
      {/* Top Cockpit Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 py-3 flex items-center justify-between shrink-0 sticky top-0 z-20">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
            BA
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white flex items-center gap-2">
              Contact Center Agent Assist Cockpit
              <Badge variant="outline" className="border-blue-500/40 bg-blue-950/40 text-blue-300 text-[10px]">
                Active Session
              </Badge>
              {connectionState === "connected" && (
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" title="WebSocket Live Connected" />
              )}
            </h1>
            <p className="text-xs text-slate-400 font-mono">Session: {sessionId} • Agent ID: AGENT-4029</p>
          </div>
        </div>

        {/* Live Call Telemetry & Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs font-mono bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
            <Clock className="h-3.5 w-3.5 text-blue-400 animate-spin" />
            <span className="text-slate-300">Duration:</span>
            <span className="font-semibold text-white">{formatDuration(callDuration)}</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsEvidenceDrawerOpen(true)}
            className="text-xs border-indigo-500/40 bg-indigo-950/30 text-indigo-300 hover:bg-indigo-900/40 cursor-pointer"
          >
            <Layers className="h-3.5 w-3.5 mr-1" />
            Evidence ({evidenceList.length})
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsSummaryModalOpen(true)}
            className="text-xs border-emerald-500/40 bg-emerald-950/30 text-emerald-300 hover:bg-emerald-900/40 cursor-pointer"
          >
            <FileText className="h-3.5 w-3.5 mr-1" />
            Post-Call Wrap-up
          </Button>

          <Button
            variant={isRecording ? "secondary" : "destructive"}
            size="sm"
            onClick={toggleMic}
            className={`text-xs cursor-pointer ${isRecording ? "bg-emerald-950/60 text-emerald-300 border border-emerald-500/40" : ""}`}
          >
            {isRecording ? (
              <>
                <Mic className="h-3.5 w-3.5 mr-1 text-emerald-400 animate-pulse" />
                Mic 16kHz ({Math.round(audioLevel * 100)}%)
              </>
            ) : (
              <>
                <MicOff className="h-3.5 w-3.5 mr-1" /> Muted
              </>
            )}
          </Button>

          <Button
            variant="destructive"
            size="sm"
            onClick={() => setIsSummaryModalOpen(true)}
            className="text-xs bg-rose-600 hover:bg-rose-500 cursor-pointer"
          >
            <PhoneOff className="h-3.5 w-3.5 mr-1" /> End Session
          </Button>
        </div>
      </header>

      {/* 3-Column Cockpit Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 overflow-hidden">
        {/* ================= COLUMN 1: Customer Profile & Context (3 cols) ================= */}
        <div className="lg:col-span-3 flex flex-col space-y-4 overflow-y-auto">
          <CustomerContextPanel
            onApplyOverride={() => {
              setInputText("I have verified your identity, Sarah, and placed an immediate 24-hour temporary geographic override on terminal 4821.");
            }}
            onRegisterTravel={() => {
              setInputText("I have registered a 30-day travel authorization for France and the Schengen region.");
            }}
            onInspectEvidence={() => setIsEvidenceDrawerOpen(true)}
          />
        </div>

        {/* ================= COLUMN 2: Live Transcript & Interaction Stream (5 cols) ================= */}
        <div className="lg:col-span-5 flex flex-col space-y-3 overflow-hidden">
          <div className="flex-1 flex flex-col overflow-hidden">
            <TranscriptTimeline
              turns={turns}
              partialCustomerText={partialCustomerText}
              partialAgentText={partialAgentText}
              className="flex-1"
            />
          </div>

          {/* Manual Agent Input Footer */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-2 shrink-0">
            <input
              type="text"
              className="flex-1 h-9 rounded-lg bg-slate-950 border border-slate-700 px-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              placeholder="Type message or edit suggested response before sending..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendManual()}
            />
            <Button size="sm" onClick={handleSendManual} className="text-xs h-9 cursor-pointer">
              <Send className="h-3.5 w-3.5 mr-1" /> Send
            </Button>
          </div>
        </div>

        {/* ================= COLUMN 3: Real-Time Assist Guidance & Grounding (4 cols) ================= */}
        <div className="lg:col-span-4 flex flex-col space-y-3.5 overflow-y-auto">
          {/* Quick Scenario Selector Bar for Live Grounding & Intent Simulation */}
          <div className="flex items-center gap-1 p-1.5 rounded-lg bg-slate-950/60 border border-slate-800/80 overflow-x-auto text-[11px] shrink-0">
            <span className="text-[10px] text-slate-400 font-mono pl-1 uppercase tracking-wider shrink-0 flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-blue-400" />
              Scenario:
            </span>
            <button
              onClick={() => simulateScenario("card_declined")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer whitespace-nowrap ${
                activeIntent === "card_declined" && groundingState === "GROUNDED" && !isDegraded
                  ? "bg-emerald-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Grounded
            </button>
            <button
              onClick={() => simulateScenario("policy_review")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer whitespace-nowrap ${
                groundingState === "POLICY_REVIEW_NEEDED"
                  ? "bg-amber-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Policy Review
            </button>
            <button
              onClick={() => simulateScenario("missing_evidence")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer whitespace-nowrap ${
                groundingState === "MISSING_EVIDENCE"
                  ? "bg-purple-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Missing Evid
            </button>
            <button
              onClick={() => simulateScenario("out_of_scope")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer whitespace-nowrap ${
                groundingState === "LOW_CONFIDENCE"
                  ? "bg-rose-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Low Conf
            </button>
            <button
              onClick={() => simulateScenario("fee_dispute")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer whitespace-nowrap ${
                activeIntent === "fee_dispute"
                  ? "bg-indigo-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Fee Dispute
            </button>
            <button
              onClick={() => simulateScenario("degraded")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer whitespace-nowrap ${
                isDegraded
                  ? "bg-cyan-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Fallback
            </button>
          </div>

          {/* Issue & Intent Detection Card (P4.11 IntentChip with ExemplarDrawer) */}
          <IntentChip
            intentLabel={activeIntent}
            confidence={activeConfidence}
            isOutOfScope={isOutOfScope}
            degraded={isDegraded}
            triggeredByText={lastCustomerUtterance}
            candidates={intentCandidates}
            exemplarIds={exemplarIds}
          />

          {/* Grounding Safety Banner (P5.12) */}
          <GroundingBanner
            state={groundingState}
            warningMessage={warningMessage}
            onInspectEvidence={() => setIsEvidenceDrawerOpen(true)}
          />

          {/* Next-Best Action Checklist Card (P5.13) */}
          <NextBestActionCard
            title={nbaTitle}
            description={nbaDescription}
            actionType={nbaActionType}
            steps={nbaSteps}
            groundingState={groundingState}
            citations={nbaCitations}
            isFallback={isDegraded}
            onCitationClick={handleCitationClick}
          />

          {/* Suggested Agent Response Card (P5.14) */}
          <SuggestedResponseCard
            initialText={suggestedText}
            rationale={suggestedRationale}
            groundingState={groundingState}
            citations={nbaCitations}
            onInsert={(text) => setInputText(text)}
            onCitationClick={handleCitationClick}
          />
        </div>
      </div>

      {/* Slide-over Evidence Drawer (P5.15) */}
      <EvidenceDrawer
        open={isEvidenceDrawerOpen}
        onOpenChange={setIsEvidenceDrawerOpen}
        evidence={evidenceList}
        selectedCitationId={selectedCitationId}
        groundingState={groundingState}
      />

      {/* Post-Call Summary Modal (P5.16) */}
      <SummaryModal
        open={isSummaryModalOpen}
        onOpenChange={setIsSummaryModalOpen}
        sessionId={sessionId}
        onSaveToCrm={(note) => {
          console.log("CRM Note saved:", note);
          navigate("/");
        }}
      />
    </div>
  );
}
