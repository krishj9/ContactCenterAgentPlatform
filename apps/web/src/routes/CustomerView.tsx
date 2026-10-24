/**
 * Customer Voice & Chat Interface (/customer).
 *
 * Implements real-time Web Audio API capture with AudioWorklet downsampling,
 * HTML5 canvas waveform visualization, and strictly isolated conversation bubbles (R9, R14).
 */

import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mic,
  MicOff,
  Send,
  PhoneOff,
  ArrowLeft,
  ShieldCheck,
  UserCheck,
  Radio,
  Wifi,
  WifiOff,
} from "lucide-react";
import { WaveformVisualizer } from "@/components/customer/WaveformVisualizer";
import { useAudioWorklet } from "@/audio/useAudioWorklet";
import { WebSocketClient, type ConnectionState } from "@/services/websocket";
import type { TranscriptPartialEvent, TranscriptFinalEvent } from "@/types/contracts";

interface ChatBubble {
  id: string;
  speaker: "customer" | "agent";
  text: string;
  time: string;
  isPartial?: boolean;
}

export default function CustomerView() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get("session_id") || "sess_card_declined_101";

  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<ChatBubble[]>([
    {
      id: "msg_1",
      speaker: "agent",
      text: "Hello Sarah! Thank you for calling Premier Card Support. My name is Alex. How can I assist you with your account today?",
      time: "10:14 AM",
    },
    {
      id: "msg_2",
      speaker: "customer",
      text: "Hi Alex, I'm currently traveling in Europe and my Sapphire card was just declined at a restaurant in Paris. I need to pay the bill right now.",
      time: "10:14 AM",
    },
    {
      id: "msg_3",
      speaker: "agent",
      text: "I completely understand how urgent that is while abroad. Let me pull up your account security logs right away and check the fraud trigger.",
      time: "10:14 AM",
    },
  ]);
  const [partialCustomerText, setPartialCustomerText] = useState<string>("");

  const wsClientRef = useRef<WebSocketClient | null>(null);

  // Initialize WebSocket Client
  useEffect(() => {
    const client = new WebSocketClient({
      sessionId,
      role: "customer",
      participantId: "customer_sarah",
      autoConnect: true,
    });
    wsClientRef.current = client;

    const unsubState = client.onStateChange((state) => {
      setConnectionState(state);
    });

    const unsubPartial = client.on<TranscriptPartialEvent>("transcript.partial", (evt) => {
      if (evt.speaker === "customer") {
        setPartialCustomerText(evt.text);
      }
    });

    const unsubFinal = client.on<TranscriptFinalEvent>("transcript.final", (evt) => {
      if (evt.speaker === "customer") {
        setPartialCustomerText("");
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `turn_${evt.turn_id}_${Date.now()}`,
          speaker: evt.speaker as "customer" | "agent",
          text: evt.text,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    });

    return () => {
      unsubState();
      unsubPartial();
      unsubFinal();
      client.disconnect();
    };
  }, [sessionId]);

  // AudioWorklet hook
  const { isRecording, audioLevel, analyserNode, startRecording, stopRecording } = useAudioWorklet({
    onAudioChunk: (pcmBuffer, seq) => {
      if (wsClientRef.current) {
        wsClientRef.current.sendAudioChunk(pcmBuffer, seq);
      }
    },
  });

  const toggleMicrophone = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  const handleSendText = () => {
    if (!inputText.trim()) return;
    const text = inputText.trim();

    // Optimistically append to local bubbles
    const newMsg: ChatBubble = {
      id: `msg_${Date.now()}`,
      speaker: "customer",
      text,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputText("");

    // Send over WebSocket if connected
    if (wsClientRef.current) {
      wsClientRef.current.send({
        type: "transcript.manual",
        event_id: `evt_${Date.now()}`,
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        speaker: "customer",
        text,
      });
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between font-sans">
      {/* Top Customer Header */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur-md px-6 py-3.5 flex items-center justify-between sticky top-0 z-20">
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
              {connectionState === "connected" ? (
                <Badge variant="outline" className="border-emerald-500/40 bg-emerald-950/40 text-emerald-300 text-[10px] flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Live Connected
                </Badge>
              ) : connectionState === "connecting" ? (
                <Badge variant="outline" className="border-amber-500/40 bg-amber-950/40 text-amber-300 text-[10px] flex items-center gap-1">
                  <Wifi className="h-3 w-3 animate-spin text-amber-400" />
                  Connecting...
                </Badge>
              ) : (
                <Badge variant="outline" className="border-slate-700 bg-slate-800 text-slate-400 text-[10px] flex items-center gap-1">
                  <WifiOff className="h-3 w-3" />
                  Offline
                </Badge>
              )}
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
            className="text-xs bg-rose-600 hover:bg-rose-500"
          >
            <PhoneOff className="h-3.5 w-3.5 mr-1" /> End Call
          </Button>
        </div>
      </header>

      {/* Main Conversation Container */}
      <main className="max-w-3xl mx-auto w-full flex-1 flex flex-col p-6 overflow-hidden">
        {/* Customer Profile Banner */}
        <div className="mb-4 p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between text-xs shadow-md">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold">
              <UserCheck className="h-4 w-4" />
            </div>
            <div>
              <p className="font-semibold text-slate-100">Sarah Jenkins</p>
              <p className="text-slate-400 font-mono text-[11px]">Sapphire Preferred •••• 4821 (Platinum)</p>
            </div>
          </div>
          <Badge variant="outline" className="text-emerald-400 border-emerald-500/40 bg-emerald-950/20 text-[10px] flex items-center gap-1">
            <ShieldCheck className="h-3 w-3" /> Level 3 Verified
          </Badge>
        </div>

        {/* Real-time Waveform Canvas Visualizer (P6.6) */}
        <div className="mb-3">
          <WaveformVisualizer
            analyserNode={analyserNode}
            isActive={isRecording}
            audioLevel={audioLevel}
            height={70}
          />
        </div>

        {/* Live Conversation Transcript Feed */}
        <Card className="flex-1 flex flex-col overflow-hidden bg-slate-900/50 border-slate-800 shadow-xl">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Radio className={`h-3.5 w-3.5 ${isRecording ? "text-emerald-400 animate-pulse" : "text-slate-500"}`} />
              Live Spoken & Text Dialogue
            </CardTitle>
            <span className="text-[10px] font-mono text-slate-400">
              {messages.length} utterances
            </span>
          </CardHeader>

          <CardContent
            role="log"
            aria-live="polite"
            aria-label="Live conversation dialogue history"
            tabIndex={0}
            className="flex-1 overflow-y-auto p-4 space-y-3.5 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-700"
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.speaker === "customer" ? "items-end" : "items-start"}`}
              >
                <div className="flex items-center gap-1.5 mb-1 text-[11px] text-slate-400">
                  <span className={`font-semibold ${msg.speaker === "customer" ? "text-blue-400" : "text-emerald-400"}`}>
                    {msg.speaker === "customer" ? "You" : "Agent Alex (Customer Specialist)"}
                  </span>
                  <span>•</span>
                  <span className="font-mono text-[10px]">{msg.time}</span>
                </div>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                    msg.speaker === "customer"
                      ? "bg-blue-600 text-white rounded-tr-sm shadow-md shadow-blue-600/10"
                      : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-tl-sm shadow-sm"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {/* Interim Partial Speech Turn */}
            {partialCustomerText && (
              <div className="flex flex-col items-end animate-pulse" aria-live="assertive">
                <div className="flex items-center gap-1.5 mb-1 text-[11px] text-blue-400">
                  <span className="font-semibold">You (Speaking...)</span>
                </div>
                <div className="max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed bg-blue-600/40 text-blue-200 border border-blue-500/50 rounded-tr-sm">
                  {partialCustomerText}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Input Bar & Real-Time Mic Controls */}
        <div className="mt-3.5 flex items-center gap-2" role="region" aria-label="Message composition controls">
          <Button
            type="button"
            variant={isRecording ? "destructive" : "secondary"}
            size="icon"
            className={`h-11 w-11 shrink-0 rounded-xl transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
              isRecording
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 ring-2 ring-rose-500/40"
                : "bg-slate-800 hover:bg-slate-700 text-slate-200"
            }`}
            onClick={toggleMicrophone}
            title={isRecording ? "Mute Microphone" : "Start Live 16kHz Microphone"}
            aria-label={isRecording ? "Mute live microphone" : "Start live 16kHz microphone"}
          >
            {isRecording ? (
              <Mic className="h-5 w-5 animate-pulse" />
            ) : (
              <MicOff className="h-5 w-5 text-slate-400" />
            )}
          </Button>

          <input
            type="text"
            className="flex-1 h-11 rounded-xl bg-slate-900/90 border border-slate-700/80 px-4 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500 transition"
            placeholder="Type your message or speak naturally into your mic..."
            aria-label="Type your message to customer specialist"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendText()}
          />

          <Button
            type="button"
            variant="default"
            className="h-11 px-5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20 cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
            onClick={handleSendText}
            aria-label="Send message"
          >
            <Send className="h-4 w-4 mr-1.5" /> Send
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
