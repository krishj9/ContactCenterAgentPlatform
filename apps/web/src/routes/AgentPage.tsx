import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mic,
  MicOff,
  Send,
  PhoneOff,
  User,
  Clock,
  ChevronRight,
  FileText,
  Layers,
} from "lucide-react";
import { IntentChip } from "@/components/agent/IntentChip";
import { GroundingBanner } from "@/components/agent/GroundingBanner";
import { NextBestActionCard, type ActionStepItem } from "@/components/agent/NextBestActionCard";
import { SuggestedResponseCard } from "@/components/agent/SuggestedResponseCard";
import { EvidenceDrawer } from "@/components/agent/EvidenceDrawer";
import { SummaryModal } from "@/components/agent/SummaryModal";
import type {
  IntentCandidatePayload,
  GroundingStatus,
  EvidenceItemPayload,
} from "@/types/contracts";

interface Turn {
  id: number;
  speaker: "agent" | "customer";
  text: string;
  time: string;
}

export default function AgentPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get("session_id") || "sess_card_declined_101";

  const [callDuration, setCallDuration] = useState(128); // seconds
  const [isMicActive, setIsMicActive] = useState(true);
  const [inputText, setInputText] = useState("");

  // Modals & Drawers
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState(false);
  const [selectedCitationId, setSelectedCitationId] = useState<string | null>(null);
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);

  // Real-time intent detection state (P4.11)
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

  // Grounding & Assist State (P5)
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

  const [turns, setTurns] = useState<Turn[]>([
    {
      id: 1,
      speaker: "agent",
      text: "Hello, thank you for calling Premier Card Support. My name is Alex. How can I help you today?",
      time: "10:14:02",
    },
    {
      id: 2,
      speaker: "customer",
      text: "Hi Alex, I'm currently in France and my Sapphire card was just declined at a restaurant in Paris. I need to pay the bill right now.",
      time: "10:14:18",
    },
    {
      id: 3,
      speaker: "agent",
      text: "I completely understand how urgent this is while traveling abroad. Let me check your account security activity right away.",
      time: "10:14:35",
    },
  ]);

  // Timer simulation
  useEffect(() => {
    const timer = setInterval(() => setCallDuration((d) => d + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDuration = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleSendTurn = () => {
    if (!inputText.trim()) return;
    const newTurn: Turn = {
      id: turns.length + 1,
      speaker: "agent",
      text: inputText.trim(),
      time: new Date().toLocaleTimeString(),
    };
    setTurns([...turns, newTurn]);
    setInputText("");
  };

  const handleCitationClick = (citationId: string) => {
    setSelectedCitationId(citationId);
    setIsEvidenceDrawerOpen(true);
  };

  const simulateScenario = (
    scenarioKey:
      | "card_declined"
      | "fee_dispute"
      | "travel_notice"
      | "policy_review"
      | "missing_evidence"
      | "out_of_scope"
      | "degraded"
  ) => {
    switch (scenarioKey) {
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
            snippet:
              "Section 1.2: Cardholders maintaining Level 2 or 3 tenure with fewer than two waivers in 12 months qualify for immediate frontline courtesy credits up to $50.00.",
            similarity_score: 0.875,
            source_uri: "policy/fee_waiver_guidelines.pdf#section=1.2",
            risk_level: "MEDIUM",
          },
          {
            chunk_id: "pol_fee_dispute_02_s3_c2",
            store_type: "policy",
            title: "Operational Policy: Fee Escalations & Executive Override",
            snippet:
              "Section 3.2: Any dispute above $50.00 requires supervisor tier sign-off before balance adjustment.",
            similarity_score: 0.71,
            source_uri: "policy/fee_waiver_guidelines.pdf#section=3.2",
            risk_level: "HIGH",
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
        setIntentCandidates([
          { intent_label: "card_declined", confidence: 0.72 },
          { intent_label: "general_inquiry", confidence: 0.18 },
        ]);
        setExemplarIds(["ex-card_declined-1"]);
        setLastCustomerUtterance("My card declined, but I'm not sure if it was my PIN or the machine.");
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
          {
            id: "step-3",
            step_number: 3,
            text: "Escalate to Risk Operations Desk if customer requires immediate payment assistance.",
            action_type: "escalate",
          },
        ]);
        setNbaCitations([]);
        setSuggestedText(
          "I can see that the transaction wasn't authorized, Sarah. Because this requires additional security clearance, let me verify your contact information before having our risk desk assist."
        );
        setSuggestedRationale("Restricted advice mode under Spec §3.3.3 safety invariants.");
        setEvidenceList([
          {
            chunk_id: "faq_card_declined_overseas_02",
            store_type: "faq",
            title: "Customer FAQ: Foreign Card Declines",
            snippet: "General FAQ explanation of automated card declines.",
            similarity_score: 0.58,
            source_uri: "faq/card_declines.md",
            risk_level: "LOW",
          },
        ]);
        break;

      case "missing_evidence":
        setActiveIntent("card_payment_not_recognised");
        setActiveConfidence(0.61);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setGroundingState("MISSING_EVIDENCE");
        setWarningMessage("No retrieved chunks exceeded the evidence threshold (τ_evidence = 0.48). Operational actions suppressed.");
        setIntentCandidates([
          { intent_label: "card_payment_not_recognised", confidence: 0.61 },
          { intent_label: "general_inquiry", confidence: 0.39 },
        ]);
        setExemplarIds([]);
        setLastCustomerUtterance("There is a strange charge on my account from a merchant named Alpha Beta.");
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
          {
            id: "step-2",
            step_number: 2,
            text: "Transfer caller to Specialized Fraud Intake queue.",
            action_type: "escalate",
          },
        ]);
        setNbaCitations([]);
        setSuggestedText(
          "I understand you don't recognize this charge on your statement, Sarah. I am documenting the merchant details now and will connect you with our fraud intake team."
        );
        setSuggestedRationale("Fallback to general intake playbook.");
        setEvidenceList([]);
        break;

      case "out_of_scope":
        setActiveIntent("out_of_scope");
        setActiveConfidence(0.975);
        setIsOutOfScope(true);
        setIsDegraded(false);
        setGroundingState("LOW_CONFIDENCE");
        setWarningMessage("Query is out of scope. Automated procedural playbooks disabled.");
        setIntentCandidates([
          { intent_label: "out_of_scope", confidence: 0.975 },
          { intent_label: "general_inquiry", confidence: 0.015 },
          { intent_label: "card_declined", confidence: 0.01 },
        ]);
        setExemplarIds(["ex-oos-1", "ex-oos-2", "ex-oos-3"]);
        setLastCustomerUtterance("What is the weather like in Paris or New York right now? Is it going to rain tomorrow?");
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
          {
            id: "step-2",
            step_number: 2,
            text: "Inquire if cardholder has any pending banking inquiries.",
            action_type: "inform",
          },
        ]);
        setNbaCitations([]);
        setSuggestedText(
          "I specialize in cardholder support and account security, Sarah! While I don't have weather data, please let me know if you need any help with your Sapphire card or transactions."
        );
        setSuggestedRationale("Polite redirect without executing banking actions.");
        setEvidenceList([]);
        break;

      case "degraded":
        setActiveIntent("card_declined");
        setActiveConfidence(0.88);
        setIsOutOfScope(false);
        setIsDegraded(true);
        setGroundingState("GROUNDED");
        setWarningMessage("Intent detected via k-NN fallback (ONNX microservice unavailable). Deterministic playbook engaged.");
        setIntentCandidates([
          { intent_label: "card_declined", confidence: 0.88 },
          { intent_label: "card_payment_not_recognised", confidence: 0.075 },
          { intent_label: "general_inquiry", confidence: 0.045 },
        ]);
        setExemplarIds(["ex-card_declined-1", "ex-card_declined-2", "ex-card_declined-3"]);
        setLastCustomerUtterance("My card was declined at checkout due to an unexpected block.");
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
          {
            id: "step-2",
            step_number: 2,
            text: "Apply 24h temporary geographic security override on card 4821.",
            action_type: "inform",
            citation_ids: ["pol_card_decline_01_s4_c1"],
          },
          {
            id: "step-3",
            step_number: 3,
            text: "Register international travel notice for customer journey.",
            action_type: "inform",
            citation_ids: ["pol_travel_notice_03_s2_c1"],
          },
        ]);
        setNbaCitations(["pol_card_decline_01_s4_c1", "pol_travel_notice_03_s2_c1"]);
        setSuggestedText(
          "I see your card was declined at the terminal. I have confirmed your account security and can place a temporary override so you can retry the transaction immediately."
        );
        setSuggestedRationale("Deterministic fallback playbook execution.");
        setEvidenceList([
          {
            chunk_id: "pol_card_decline_01_s4_c1",
            store_type: "policy",
            title: "Operational Policy: Card Authorization & Geographic Security Rules",
            snippet:
              "Section 4.1: When a cardholder contacts support regarding a real-time transaction decline abroad, the agent must authenticate Level 3 identity.",
            similarity_score: 0.85,
            source_uri: "policy/card_authorization_v2.pdf",
            risk_level: "LOW",
          },
        ]);
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
            className="text-xs border-indigo-500/40 bg-indigo-950/30 text-indigo-300 hover:bg-indigo-900/40"
          >
            <Layers className="h-3.5 w-3.5 mr-1" />
            Evidence ({evidenceList.length})
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsSummaryModalOpen(true)}
            className="text-xs border-emerald-500/40 bg-emerald-950/30 text-emerald-300 hover:bg-emerald-900/40"
          >
            <FileText className="h-3.5 w-3.5 mr-1" />
            Post-Call Wrap-up
          </Button>

          <Button
            variant={isMicActive ? "secondary" : "destructive"}
            size="sm"
            onClick={() => setIsMicActive(!isMicActive)}
            className="text-xs"
          >
            {isMicActive ? (
              <>
                <Mic className="h-3.5 w-3.5 mr-1 text-emerald-400" /> Mic 16kHz
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
            className="text-xs bg-rose-600 hover:bg-rose-500"
          >
            <PhoneOff className="h-3.5 w-3.5 mr-1" /> End Session
          </Button>
        </div>
      </header>

      {/* 3-Column Cockpit Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 overflow-hidden">
        {/* ================= COLUMN 1: Customer Profile & Context (3 cols) ================= */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          {/* Customer Profile Card */}
          <Card className="bg-slate-900/60 border-slate-800 shadow-md">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                  <User className="h-4 w-4 text-blue-400" /> Customer Context
                </CardTitle>
                <Badge variant="outline" className="text-[10px] border-emerald-500/40 text-emerald-400 bg-emerald-950/20">
                  Platinum Tier
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div>
                <p className="text-slate-400">Account Holder</p>
                <p className="font-medium text-slate-100 text-sm">Sarah Jenkins</p>
              </div>
              <div>
                <p className="text-slate-400">Primary Product</p>
                <p className="font-medium text-slate-200">Sapphire Preferred Visa Signature</p>
                <p className="font-mono text-slate-400 text-[11px]">•••• •••• •••• 4821</p>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/60">
                <div>
                  <p className="text-slate-400">Relationship</p>
                  <p className="font-medium text-slate-200">7 Years</p>
                </div>
                <div>
                  <p className="text-slate-400">Authentication</p>
                  <p className="font-medium text-emerald-400 flex items-center gap-1">
                    Level 3 Verified
                  </p>
                </div>
              </div>
              <div className="pt-2 border-t border-slate-800/60">
                <p className="text-slate-400 mb-1">Context Summary</p>
                <p className="text-slate-300 text-[11px] leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
                  Customer departed US on Oct 20. Automated security rule triggered on foreign POS terminal (Paris, France - EUR 142.50). No prior travel notice logged.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions / Verification Card */}
          <Card className="bg-slate-900/60 border-slate-800 flex-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-slate-300">Quick Agent Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <button
                onClick={() => {
                  setInputText("I have applied a temporary 24-hour geographic override to terminal 4821.");
                }}
                className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition flex items-center justify-between cursor-pointer"
              >
                <span>Temporary Geographic Override</span>
                <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
              </button>
              <button
                onClick={() => {
                  setInputText("I have registered a 30-day travel authorization for France and the Schengen region.");
                }}
                className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition flex items-center justify-between cursor-pointer"
              >
                <span>Register Travel Notice (30 Days)</span>
                <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
              </button>
              <button
                onClick={() => setIsEvidenceDrawerOpen(true)}
                className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition flex items-center justify-between cursor-pointer"
              >
                <span>Inspect Policy Lineage Chunks</span>
                <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
              </button>
            </CardContent>
          </Card>
        </div>

        {/* ================= COLUMN 2: Live Transcript & Interaction Stream (5 cols) ================= */}
        <div className="lg:col-span-5 flex flex-col space-y-3 overflow-hidden">
          <Card className="flex-1 flex flex-col bg-slate-900/60 border-slate-800 overflow-hidden shadow-lg">
            <CardHeader className="py-2.5 px-4 border-b border-slate-800 bg-slate-900/90 flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></div>
                <CardTitle className="text-xs font-semibold text-slate-200">
                  Live Spoken & Text Transcript
                </CardTitle>
              </div>
              <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-700">
                Turn {turns.length}
              </Badge>
            </CardHeader>

            {/* Transcript turns feed */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-3.5">
              {turns.map((t) => (
                <div
                  key={t.id}
                  className={`flex flex-col ${t.speaker === "agent" ? "items-end" : "items-start"}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 text-[11px] text-slate-400">
                    <span
                      className={`font-semibold ${
                        t.speaker === "agent" ? "text-blue-400" : "text-emerald-400"
                      }`}
                    >
                      {t.speaker === "agent" ? "Agent (You)" : "Customer (Sarah)"}
                    </span>
                    <span>•</span>
                    <span className="font-mono text-[10px]">{t.time}</span>
                  </div>
                  <div
                    className={`max-w-[90%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                      t.speaker === "agent"
                        ? "bg-blue-600 text-white rounded-tr-sm"
                        : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-tl-sm shadow-sm"
                    }`}
                  >
                    {t.text}
                  </div>
                </div>
              ))}
            </CardContent>

            {/* Manual Agent Input */}
            <CardFooter className="p-3 border-t border-slate-800 bg-slate-900/80 gap-2">
              <input
                type="text"
                className="flex-1 h-9 rounded-lg bg-slate-950 border border-slate-700 px-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="Type response or edit suggestion before sending..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendTurn()}
              />
              <Button size="sm" onClick={handleSendTurn} className="text-xs h-9">
                <Send className="h-3.5 w-3.5 mr-1" /> Send
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* ================= COLUMN 3: Real-Time Assist Guidance & Grounding (4 cols) ================= */}
        <div className="lg:col-span-4 flex flex-col space-y-3.5 overflow-y-auto">
          {/* Quick Scenario Selector Bar for Live Grounding & Intent Simulation */}
          <div className="flex items-center gap-1 p-1.5 rounded-lg bg-slate-950/60 border border-slate-800/80 overflow-x-auto text-[11px] shrink-0">
            <span className="text-[10px] text-slate-400 font-mono pl-1 uppercase tracking-wider shrink-0">
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
              Low Conf (OOS)
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
              k-NN Fallback
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
