import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mic,
  MicOff,
  Send,
  PhoneOff,
  Copy,
  Check,
  ShieldCheck,
  AlertTriangle,
  FileText,
  User,
  Clock,
  ChevronRight,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  Edit3,
} from "lucide-react";
import { IntentChip } from "@/components/agent/IntentChip";
import type { IntentCandidatePayload } from "@/types/contracts";

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
  const [suggestedText, setSuggestedText] = useState(
    "I see the automated security trigger on your Sapphire card from a transaction in Paris, Sarah. I have verified your identity and can lift this geographic hold immediately so you can complete your payment."
  );
  const [copied, setCopied] = useState(false);
  const [disposition, setDisposition] = useState<"accepted" | "edited" | "dismissed" | null>(null);

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

  const simulateScenario = (scenarioKey: "card_declined" | "fee_dispute" | "travel_notice" | "out_of_scope" | "degraded") => {
    switch (scenarioKey) {
      case "card_declined":
        setActiveIntent("card_declined");
        setActiveConfidence(0.942);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setIntentCandidates([
          { intent_label: "card_declined", confidence: 0.942 },
          { intent_label: "country_support", confidence: 0.038 },
          { intent_label: "general_inquiry", confidence: 0.02 },
        ]);
        setExemplarIds(["ex-card_declined-1", "ex-card_declined-2", "ex-card_declined-3"]);
        setLastCustomerUtterance("Hi Alex, I'm currently in France and my Sapphire card was just declined at a restaurant in Paris. I need to pay the bill right now.");
        break;
      case "fee_dispute":
        setActiveIntent("fee_dispute");
        setActiveConfidence(0.918);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setIntentCandidates([
          { intent_label: "fee_dispute", confidence: 0.918 },
          { intent_label: "card_payment_fee_charged", confidence: 0.052 },
          { intent_label: "general_inquiry", confidence: 0.03 },
        ]);
        setExemplarIds(["ex-fee_dispute-1", "ex-fee_dispute-2", "ex-fee_dispute-3"]);
        setLastCustomerUtterance("I noticed an overdraft fee of thirty-five dollars charged to my statement yesterday. Can this fee be waived?");
        break;
      case "travel_notice":
        setActiveIntent("travel_notice");
        setActiveConfidence(0.965);
        setIsOutOfScope(false);
        setIsDegraded(false);
        setIntentCandidates([
          { intent_label: "travel_notice", confidence: 0.965 },
          { intent_label: "country_support", confidence: 0.025 },
          { intent_label: "general_inquiry", confidence: 0.01 },
        ]);
        setExemplarIds(["ex-travel_notice-1", "ex-travel_notice-2", "ex-travel_notice-3"]);
        setLastCustomerUtterance("I am traveling to Tokyo next week and need to make sure my card is authorized for international purchases.");
        break;
      case "out_of_scope":
        setActiveIntent("out_of_scope");
        setActiveConfidence(0.975);
        setIsOutOfScope(true);
        setIsDegraded(false);
        setIntentCandidates([
          { intent_label: "out_of_scope", confidence: 0.975 },
          { intent_label: "general_inquiry", confidence: 0.015 },
          { intent_label: "card_declined", confidence: 0.01 },
        ]);
        setExemplarIds(["ex-oos-1", "ex-oos-2", "ex-oos-3"]);
        setLastCustomerUtterance("What is the weather like in Paris or New York right now? Is it going to rain tomorrow?");
        break;
      case "degraded":
        setActiveIntent("card_declined");
        setActiveConfidence(0.880);
        setIsOutOfScope(false);
        setIsDegraded(true);
        setIntentCandidates([
          { intent_label: "card_declined", confidence: 0.880 },
          { intent_label: "card_payment_not_recognised", confidence: 0.075 },
          { intent_label: "general_inquiry", confidence: 0.045 },
        ]);
        setExemplarIds(["ex-card_declined-1", "ex-card_declined-2", "ex-card_declined-3"]);
        setLastCustomerUtterance("My card was declined at checkout due to an unexpected block.");
        break;
    }
  };

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

  const handleCopySuggestion = () => {
    navigator.clipboard.writeText(suggestedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleInsertSuggestion = () => {
    setInputText(suggestedText);
    setDisposition("accepted");
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col">
      {/* Top Cockpit Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
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
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs font-mono bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
            <Clock className="h-3.5 w-3.5 text-blue-400 animate-spin" />
            <span className="text-slate-300">Call Duration:</span>
            <span className="font-semibold text-white">{formatDuration(callDuration)}</span>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant={isMicActive ? "secondary" : "destructive"}
              size="sm"
              onClick={() => setIsMicActive(!isMicActive)}
              className="text-xs"
            >
              {isMicActive ? (
                <>
                  <Mic className="h-3.5 w-3.5 mr-1 text-emerald-400" /> Mic 16kHz Active
                </>
              ) : (
                <>
                  <MicOff className="h-3.5 w-3.5 mr-1" /> Mic Muted
                </>
              )}
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => navigate("/")}
              className="text-xs"
            >
              <PhoneOff className="h-3.5 w-3.5 mr-1" /> End Session
            </Button>
          </div>
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
                    <ShieldCheck className="h-3 w-3" /> Level 3 Verified
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
              <button className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition flex items-center justify-between cursor-pointer">
                <span>Temporary Geographic Override</span>
                <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
              </button>
              <button className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition flex items-center justify-between cursor-pointer">
                <span>Register Travel Notice (30 Days)</span>
                <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
              </button>
              <button className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition flex items-center justify-between cursor-pointer">
                <span>View Real-time Auth Declines</span>
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
        <div className="lg:col-span-4 flex flex-col space-y-4 overflow-y-auto">
          {/* Quick Scenario Selector Bar for Live Intent Simulation */}
          <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-slate-950/60 border border-slate-800/80 overflow-x-auto text-[11px]">
            <span className="text-[10px] text-slate-400 font-mono pl-1 uppercase tracking-wider shrink-0">
              Test Scenario:
            </span>
            <button
              onClick={() => simulateScenario("card_declined")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer ${
                activeIntent === "card_declined" && !isDegraded
                  ? "bg-purple-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Card Decline
            </button>
            <button
              onClick={() => simulateScenario("fee_dispute")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer ${
                activeIntent === "fee_dispute"
                  ? "bg-purple-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Fee Dispute
            </button>
            <button
              onClick={() => simulateScenario("travel_notice")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer ${
                activeIntent === "travel_notice"
                  ? "bg-purple-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              Travel Notice
            </button>
            <button
              onClick={() => simulateScenario("out_of_scope")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer ${
                isOutOfScope
                  ? "bg-rose-600 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-white"
              }`}
            >
              OOS Chit-Chat
            </button>
            <button
              onClick={() => simulateScenario("degraded")}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all cursor-pointer ${
                isDegraded
                  ? "bg-amber-600 text-white font-semibold shadow-sm"
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

          {/* Active Safety Guardrail Alert Banner */}
          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
            <span className="text-[11px] leading-tight">
              <strong>Safety Guardrail Active:</strong> Autonomous actions disabled (R14). Guidance presented as editable suggestion.
            </span>
          </div>

          {/* Next-Best Action (NBA) Card */}
          <Card className="bg-slate-900/80 border-blue-500/30 shadow-md">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" /> Next-Best Action
                </CardTitle>
                <Badge variant="grounded" className="text-[10px]">
                  GROUNDED
                </Badge>
              </div>
              <CardDescription className="text-slate-300 font-medium text-xs mt-1">
                Lift Geographic Decline & Register Travel Notice
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Step 1: Confirm POS location with cardholder (Paris, France).<br />
                Step 2: Lift 24h fraud hold on card terminal 4821.<br />
                Step 3: Register 30-day travel notice for France & Schengen area.
              </p>
              {/* Policy Chunk Lineage Citations */}
              <div className="pt-2 border-t border-slate-800">
                <p className="text-[10px] text-slate-400 uppercase font-semibold mb-1">Authoritative Policy Citations:</p>
                <div className="flex flex-wrap gap-1.5">
                  <span className="inline-flex items-center gap-1 text-[10px] bg-slate-800/80 text-blue-300 border border-slate-700 px-2 py-0.5 rounded">
                    POL-CARD-DECLINE-01 (sim: 0.89) <ExternalLink className="h-2.5 w-2.5" />
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] bg-slate-800/80 text-blue-300 border border-slate-700 px-2 py-0.5 rounded">
                    POL-TRAVEL-NOTICE-03 (sim: 0.84) <ExternalLink className="h-2.5 w-2.5" />
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Suggested Response (Editable HITL) */}
          <Card className="bg-slate-900/80 border-slate-800 shadow-md">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <Edit3 className="h-3.5 w-3.5 text-blue-400" /> Suggested Agent Response
                </CardTitle>
                <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-400">
                  Editable Suggestion (R14)
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <textarea
                className="w-full h-24 rounded-lg bg-slate-950 border border-slate-700 p-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 leading-relaxed resize-none"
                value={suggestedText}
                onChange={(e) => {
                  setSuggestedText(e.target.value);
                  setDisposition("edited");
                }}
              />
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Cites: POL-CARD-DECLINE-01</span>
                <div className="flex items-center space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-[11px] px-2 text-slate-300 hover:text-white"
                    onClick={handleCopySuggestion}
                  >
                    {copied ? <Check className="h-3 w-3 text-emerald-400 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    className="h-7 text-[11px] px-2.5 bg-blue-600 hover:bg-blue-500"
                    onClick={handleInsertSuggestion}
                  >
                    Use Suggestion
                  </Button>
                </div>
              </div>
            </CardContent>
            {/* Feedback / Disposition buttons (R16 HITL audit) */}
            <CardFooter className="py-2 px-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
              <span>Agent Feedback:</span>
              <div className="flex items-center space-x-1.5">
                <Button
                  variant={disposition === "accepted" ? "emerald" : "ghost"}
                  size="sm"
                  className="h-6 px-2 text-[10px]"
                  onClick={() => setDisposition("accepted")}
                >
                  <ThumbsUp className="h-3 w-3 mr-1" /> Accept
                </Button>
                <Button
                  variant={disposition === "edited" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-6 px-2 text-[10px]"
                  onClick={() => setDisposition("edited")}
                >
                  <Edit3 className="h-3 w-3 mr-1" /> Edited
                </Button>
                <Button
                  variant={disposition === "dismissed" ? "destructive" : "ghost"}
                  size="sm"
                  className="h-6 px-2 text-[10px]"
                  onClick={() => setDisposition("dismissed")}
                >
                  <ThumbsDown className="h-3 w-3 mr-1" /> Dismiss
                </Button>
              </div>
            </CardFooter>
          </Card>

          {/* Disposition & Summary Notes Card */}
          <Card className="bg-slate-900/80 border-slate-800 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-white flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-400" /> Post-Call CRM Disposition
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5 text-xs text-slate-300">
              <div className="p-2 rounded bg-slate-950/40 border border-slate-800/60 space-y-1 text-[11px]">
                <p><strong className="text-slate-400">Overview:</strong> Card declined during travel in France.</p>
                <p><strong className="text-slate-400">Actions:</strong> Verified biometrics; unlocked POS security rule.</p>
                <p><strong className="text-slate-400">Follow-up:</strong> Travel notice active through Nov 20.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
