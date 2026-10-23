import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Headphones, ShieldCheck, User, Sparkles, ArrowRight, Activity, Database, Lock } from "lucide-react";

export default function LandingPage() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState("sess_card_declined_101");
  const [selectedRole, setSelectedRole] = useState<"agent" | "customer">("agent");

  const sampleScenarios = [
    { id: "sess_card_declined_101", title: "Card Declined Abroad", intent: "card_declined", tier: "Platinum" },
    { id: "sess_fee_dispute_202", title: "Annual Fee Dispute", intent: "fee_dispute", tier: "Gold" },
    { id: "sess_travel_notice_303", title: "Travel Notice Registration", intent: "travel_notice", tier: "Premier" },
  ];

  const handleJoin = (role: "agent" | "customer", customSession?: string) => {
    const targetSession = customSession || sessionId;
    if (role === "agent") {
      navigate(`/agent?session_id=${encodeURIComponent(targetSession)}`);
    } else {
      navigate(`/customer?session_id=${encodeURIComponent(targetSession)}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] flex flex-col justify-between text-slate-100">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white tracking-tight">BankAssist Intelligence</h1>
            <p className="text-xs text-slate-400">Enterprise Contact Center AI Platform</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-950/40 text-emerald-300 flex items-center gap-1.5 py-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            pgvector HNSW Ready
          </Badge>
          <Badge variant="outline" className="border-blue-500/30 bg-blue-950/40 text-blue-300 flex items-center gap-1.5 py-1">
            <Lock className="h-3 w-3" />
            R14 Customer Isolation Enforced
          </Badge>
        </div>
      </header>

      {/* Hero & Role Gateway */}
      <main className="max-w-5xl mx-auto px-6 py-12 flex-1 flex flex-col items-center justify-center">
        <div className="text-center max-w-2xl mb-10">
          <Badge variant="secondary" className="mb-4 bg-slate-800/80 text-blue-400 border border-blue-500/20 px-3 py-1">
            Phase P2 Local Architecture
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-3">
            Real-Time Grounded Agent Assist Cockpit
          </h2>
          <p className="text-slate-400 text-sm sm:text-base">
            Providing human agents with policy-grounded Next-Best-Actions, instant retrieval, and real-time audio downsampling while isolating customers from internal assist signals.
          </p>
        </div>

        {/* Dual Role Selector Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl mb-10">
          {/* Agent Cockpit Gateway */}
          <Card
            className={`cursor-pointer transition-all border-2 ${
              selectedRole === "agent"
                ? "border-blue-500/80 bg-slate-900/90 shadow-2xl shadow-blue-500/10 ring-1 ring-blue-500/30"
                : "border-slate-800/80 bg-slate-900/50 hover:border-slate-700"
            }`}
            onClick={() => setSelectedRole("agent")}
          >
            <CardHeader className="pb-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center mb-2">
                <Headphones className="h-5 w-5 text-blue-400" />
              </div>
              <CardTitle className="text-lg">Agent Cockpit View</CardTitle>
              <CardDescription>
                Live Assist guidance, grounded Next-Best-Actions, citations, and editable suggested responses.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-xs text-slate-400 space-y-1.5 mb-4">
                <li className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                  Policy citation chunk lineage
                </li>
                <li className="flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-blue-400" />
                  Intent confidence calibration
                </li>
                <li className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-purple-400" />
                  SLO-monitored retrieval pipeline
                </li>
              </ul>
              <Button
                variant={selectedRole === "agent" ? "default" : "outline"}
                className="w-full text-xs font-medium"
                onClick={() => handleJoin("agent")}
              >
                Launch Agent Cockpit <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </CardContent>
          </Card>

          {/* Customer Voice/Chat Gateway */}
          <Card
            className={`cursor-pointer transition-all border-2 ${
              selectedRole === "customer"
                ? "border-emerald-500/80 bg-slate-900/90 shadow-2xl shadow-emerald-500/10 ring-1 ring-emerald-500/30"
                : "border-slate-800/80 bg-slate-900/50 hover:border-slate-700"
            }`}
            onClick={() => setSelectedRole("customer")}
          >
            <CardHeader className="pb-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mb-2">
                <User className="h-5 w-5 text-emerald-400" />
              </div>
              <CardTitle className="text-lg">Customer Portal View</CardTitle>
              <CardDescription>
                Clean customer voice/chat session with complete isolation from internal AI assist signals.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-xs text-slate-400 space-y-1.5 mb-4">
                <li className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                  Zero assist metadata leakage (R9/R14)
                </li>
                <li className="flex items-center gap-1.5">
                  <Headphones className="h-3.5 w-3.5 text-emerald-400" />
                  Realtime 16kHz PCM audio streaming
                </li>
                <li className="flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-emerald-400" />
                  Encrypted human-to-human channel
                </li>
              </ul>
              <Button
                variant={selectedRole === "customer" ? "emerald" : "outline"}
                className="w-full text-xs font-medium"
                onClick={() => handleJoin("customer")}
              >
                Join as Customer <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Launch Scenario Presets */}
        <div className="w-full max-w-3xl bg-slate-900/40 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 mb-2">Preset Scenario Fixtures:</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {sampleScenarios.map((sc) => (
              <button
                key={sc.id}
                onClick={() => {
                  setSessionId(sc.id);
                  handleJoin(selectedRole, sc.id);
                }}
                className="text-left p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 transition cursor-pointer"
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-200">{sc.title}</span>
                  <Badge variant="outline" className="text-[10px] py-0 border-blue-500/40 text-blue-300">
                    {sc.tier}
                  </Badge>
                </div>
                <div className="text-[11px] text-slate-400 font-mono">{sc.id}</div>
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        Contact Center Agent Helper Platform • Phase P2 • PostgreSQL 16 (pgvector) + Redis 7 + Firebase Hosting
      </footer>
    </div>
  );
}
