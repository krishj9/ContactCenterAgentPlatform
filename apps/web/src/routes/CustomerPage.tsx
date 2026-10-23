import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Mic, MicOff, Send, PhoneOff, ArrowLeft, ShieldCheck, UserCheck } from "lucide-react";

interface ChatMessage {
  id: string;
  speaker: "customer" | "agent";
  text: string;
  time: string;
}

export default function CustomerPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get("session_id") || "sess_card_declined_101";

  const [isMicActive, setIsMicActive] = useState(false);
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg_1",
      speaker: "agent",
      text: "Hello! Thank you for calling Premier Card Support. My name is Alex. How can I assist you with your account today?",
      time: "10:14 AM",
    },
    {
      id: "msg_2",
      speaker: "customer",
      text: "Hi Alex, I'm currently traveling in Europe and my Sapphire card just got declined when paying for lunch.",
      time: "10:15 AM",
    },
    {
      id: "msg_3",
      speaker: "agent",
      text: "I completely understand how stressful that is while abroad. Let me pull up your account security logs right away and check the fraud trigger.",
      time: "10:15 AM",
    },
  ]);

  const handleSend = () => {
    if (!inputText.trim()) return;
    const newMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      speaker: "customer",
      text: inputText.trim(),
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputText("");
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between">
      {/* Top Customer Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/")}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 mr-1" /> Exit
          </Button>
          <div className="h-4 w-[1px] bg-slate-800"></div>
          <div>
            <h1 className="text-sm font-semibold text-white flex items-center gap-2">
              Premier Banking Support Session
              <Badge variant="outline" className="border-emerald-500/40 bg-emerald-950/40 text-emerald-300 text-[10px]">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1"></span>
                Connected
              </Badge>
            </h1>
            <p className="text-xs text-slate-400 font-mono">Session ID: {sessionId}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/50">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>256-bit Encrypted Voice Channel</span>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => navigate("/")}
            className="text-xs"
          >
            <PhoneOff className="h-3.5 w-3.5 mr-1" /> End Call
          </Button>
        </div>
      </header>

      {/* Main Conversation Container */}
      <main className="max-w-3xl mx-auto w-full flex-1 flex flex-col p-6 overflow-hidden">
        {/* Customer Profile Banner */}
        <div className="mb-4 p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center">
              <UserCheck className="h-4 w-4" />
            </div>
            <div>
              <p className="font-medium text-slate-200">Sarah Jenkins</p>
              <p className="text-slate-400 font-mono">Sapphire Preferred •••• 4821 (Platinum)</p>
            </div>
          </div>
          <Badge variant="outline" className="text-slate-400 border-slate-700">
            Verified via Biometrics
          </Badge>
        </div>

        {/* Message Feed */}
        <Card className="flex-1 flex flex-col overflow-hidden bg-slate-900/40 border-slate-800">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800 bg-slate-900/80">
            <CardTitle className="text-xs font-medium text-slate-400">
              Live Verified Transcript
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.speaker === "customer" ? "items-end" : "items-start"}`}
              >
                <div className="flex items-center gap-1.5 mb-1 text-[11px] text-slate-400">
                  <span className="font-medium text-slate-300">
                    {msg.speaker === "customer" ? "You" : "Agent Alex (Customer Specialist)"}
                  </span>
                  <span>•</span>
                  <span>{msg.time}</span>
                </div>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.speaker === "customer"
                      ? "bg-blue-600 text-white rounded-tr-sm"
                      : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-tl-sm shadow-sm"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Input Bar & Voice Controls */}
        <div className="mt-4 flex items-center gap-2">
          <Button
            type="button"
            variant={isMicActive ? "destructive" : "secondary"}
            size="icon"
            className="h-10 w-10 shrink-0"
            onClick={() => setIsMicActive(!isMicActive)}
            title={isMicActive ? "Mute Microphone" : "Unmute Microphone"}
          >
            {isMicActive ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4 text-slate-400" />}
          </Button>
          <input
            type="text"
            className="flex-1 h-10 rounded-lg bg-slate-900/80 border border-slate-700/80 px-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            placeholder="Type your message to the agent..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <Button
            type="button"
            variant="default"
            className="h-10 px-4 text-xs font-medium"
            onClick={handleSend}
          >
            <Send className="h-3.5 w-3.5 mr-1" /> Send
          </Button>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-3 text-center text-xs text-slate-500">
        BankAssist Customer Channel • Protected by Enterprise TLS 1.3
      </footer>
    </div>
  );
}
