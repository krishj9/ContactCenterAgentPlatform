/**
 * Live Rolling Transcript Timeline (P6.8).
 *
 * Virtualized/scrollable message stream with speaker roles, timestamps,
 * partial speech pulsing indicators, and real-time keyword search highlight.
 */

import { useState, useRef, useEffect, useMemo } from "react";
import {
  Search,
  Radio,
  Clock,
  Copy,
  Check,
  User,
  Headphones,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

export interface TimelineTurn {
  id: string | number;
  turn_id?: number;
  speaker: "customer" | "agent" | "system";
  text: string;
  time: string;
  is_final?: boolean;
  duration_ms?: number;
}

export interface TranscriptTimelineProps {
  turns: TimelineTurn[];
  partialCustomerText?: string;
  partialAgentText?: string;
  className?: string;
}

export function TranscriptTimeline({
  turns,
  partialCustomerText,
  partialAgentText,
  className = "",
}: TranscriptTimelineProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState<string | number | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom on new turns
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns, partialCustomerText, partialAgentText]);

  const handleCopyTurn = (turn: TimelineTurn) => {
    navigator.clipboard.writeText(turn.text);
    setCopiedId(turn.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Keyword highlighting helper
  const renderHighlightedText = (text: string, query: string) => {
    if (!query.trim()) return text;
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escaped})`, "gi");
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark
          key={i}
          className="bg-amber-400/30 text-amber-200 px-0.5 rounded font-medium border border-amber-400/40"
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // Filtered turns and search count
  const { filteredTurns, matchCount } = useMemo(() => {
    if (!searchQuery.trim()) {
      return { filteredTurns: turns, matchCount: 0 };
    }
    const q = searchQuery.toLowerCase();
    let count = 0;
    const matched = turns.filter((t) => {
      const hasMatch = t.text.toLowerCase().includes(q);
      if (hasMatch) {
        const occurrences = (t.text.toLowerCase().match(new RegExp(q, "g")) || []).length;
        count += occurrences;
      }
      return hasMatch;
    });
    return { filteredTurns: matched, matchCount: count };
  }, [turns, searchQuery]);

  return (
    <div className={`flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-lg ${className}`}>
      {/* Timeline Header & Search Bar */}
      <div className="p-3 border-b border-slate-800 bg-slate-900/90 flex flex-col gap-2 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
            <h3 className="text-xs font-semibold text-slate-200">
              Live Spoken & Text Dialogue Timeline
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] font-mono text-slate-400 border-slate-700">
              {turns.length} Turns
            </Badge>
          </div>
        </div>

        {/* Real-time Keyword Search Bar */}
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            className="w-full h-8 pl-8 pr-16 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            placeholder="Search transcript keywords (e.g. Paris, fee, decline)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <div className="absolute right-2 flex items-center gap-1">
              <span className="text-[10px] font-mono text-amber-300 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-500/30">
                {matchCount} hit{matchCount === 1 ? "" : "s"}
              </span>
              <button
                onClick={() => setSearchQuery("")}
                className="text-slate-400 hover:text-white p-0.5 cursor-pointer"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Scrollable Message Turns */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {filteredTurns.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs">
            {searchQuery ? "No matches found for search query." : "No transcript turns yet."}
          </div>
        ) : (
          filteredTurns.map((turn, index) => {
            const isAgent = turn.speaker === "agent";
            return (
              <div
                key={turn.id || index}
                className={`flex flex-col group ${isAgent ? "items-end" : "items-start"}`}
              >
                <div className="flex items-center gap-1.5 mb-1 text-[11px] text-slate-400">
                  {isAgent ? (
                    <>
                      <Headphones className="h-3 w-3 text-blue-400" />
                      <span className="font-semibold text-blue-400">Agent (You)</span>
                    </>
                  ) : (
                    <>
                      <User className="h-3 w-3 text-emerald-400" />
                      <span className="font-semibold text-emerald-400">Customer (Sarah Jenkins)</span>
                    </>
                  )}
                  <span>•</span>
                  <span className="font-mono text-[10px] flex items-center gap-0.5">
                    <Clock className="h-2.5 w-2.5" />
                    {turn.time}
                  </span>
                  {turn.duration_ms !== undefined && turn.duration_ms > 0 && (
                    <span className="font-mono text-[9px] text-slate-500">
                      ({(turn.duration_ms / 1000).toFixed(1)}s)
                    </span>
                  )}
                  <button
                    onClick={() => handleCopyTurn(turn)}
                    className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition ml-1 p-0.5 cursor-pointer"
                    title="Copy turn text"
                  >
                    {copiedId === turn.id ? (
                      <Check className="h-3 w-3 text-emerald-400" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </button>
                </div>

                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed transition-all shadow-sm ${
                    isAgent
                      ? "bg-blue-600 text-white rounded-tr-sm shadow-blue-600/10"
                      : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-tl-sm"
                  }`}
                >
                  {renderHighlightedText(turn.text, searchQuery)}
                </div>
              </div>
            );
          })
        )}

        {/* Real-time Customer Partial Speech Stream */}
        {partialCustomerText && (
          <div className="flex flex-col items-start animate-pulse">
            <div className="flex items-center gap-1.5 mb-1 text-[11px] text-emerald-400">
              <User className="h-3 w-3 text-emerald-400" />
              <span className="font-semibold">Customer (Speaking live...)</span>
            </div>
            <div className="max-w-[88%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed bg-emerald-950/40 text-emerald-200 border border-emerald-500/50 rounded-tl-sm shadow-md">
              {renderHighlightedText(partialCustomerText, searchQuery)}
            </div>
          </div>
        )}

        {/* Real-time Agent Partial Speech Stream */}
        {partialAgentText && (
          <div className="flex flex-col items-end animate-pulse">
            <div className="flex items-center gap-1.5 mb-1 text-[11px] text-blue-400">
              <Headphones className="h-3 w-3 text-blue-400" />
              <span className="font-semibold">Agent (Speaking live...)</span>
            </div>
            <div className="max-w-[88%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed bg-blue-950/40 text-blue-200 border border-blue-500/50 rounded-tr-sm shadow-md">
              {renderHighlightedText(partialAgentText, searchQuery)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
