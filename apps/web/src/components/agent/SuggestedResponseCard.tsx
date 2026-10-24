import * as React from "react";
import {
  MessageSquare,
  Copy,
  Check,
  SendHorizontal,
  Edit3,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { GroundingStatus } from "@/types/contracts";

export interface SuggestedResponseCardProps {
  responseId?: string;
  initialText: string;
  rationale?: string;
  groundingState: GroundingStatus;
  citations?: string[];
  isEditable?: boolean;
  onCopy?: (text: string) => void;
  onInsert?: (text: string) => void;
  onDisposition?: (disposition: "accepted" | "edited" | "dismissed") => void;
  onCitationClick?: (citationId: string) => void;
  className?: string;
}

export function SuggestedResponseCard({
  initialText,
  rationale,
  groundingState,
  citations = [],
  onCopy,
  onInsert,
  onDisposition,
  onCitationClick,
  className = "",
}: SuggestedResponseCardProps) {
  const [currentText, setCurrentText] = React.useState(initialText);
  const [isCopied, setIsCopied] = React.useState(false);
  const [disposition, setDisposition] = React.useState<"accepted" | "edited" | "dismissed" | null>(null);

  // Sync when initialText changes externally (e.g. Scenario change)
  React.useEffect(() => {
    setCurrentText(initialText);
    setDisposition(null);
  }, [initialText]);

  const isDirty = currentText !== initialText;

  const handleCopy = () => {
    navigator.clipboard.writeText(currentText);
    setIsCopied(true);
    onCopy?.(currentText);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleInsert = () => {
    onInsert?.(currentText);
    handleDisposition(isDirty ? "edited" : "accepted");
  };

  const handleReset = () => {
    setCurrentText(initialText);
  };

  const handleDisposition = (status: "accepted" | "edited" | "dismissed") => {
    setDisposition(status);
    onDisposition?.(status);
  };

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/90 shadow-xl overflow-hidden backdrop-blur-md transition-all duration-300 ${className}`}
    >
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/70 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <MessageSquare className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-white tracking-wide">Suggested Agent Response</h3>
              <Badge
                variant="outline"
                className="text-[9px] font-mono border-slate-700 bg-slate-800/60 text-slate-300 flex items-center gap-1"
              >
                <Sparkles className="h-2.5 w-2.5 text-blue-400" />
                R14 HITL • {groundingState}
              </Badge>
            </div>
          </div>
        </div>

        {isDirty && (
          <button
            onClick={handleReset}
            className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-200 transition cursor-pointer"
            title="Reset to generated text"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* Rationale if present */}
      {rationale && (
        <div className="px-4 pt-2.5 pb-1 text-[11px] text-slate-400 leading-snug">
          <span className="text-indigo-400 font-medium">Strategy: </span>
          {rationale}
        </div>
      )}

      {/* Response Textarea / Editor */}
      <div className="p-3.5 pt-2">
        <div className="relative">
          <textarea
            className="w-full h-24 rounded-lg bg-slate-950/80 border border-slate-700/80 hover:border-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 p-3 text-xs text-slate-200 leading-relaxed resize-none transition focus:outline-none"
            value={currentText}
            onChange={(e) => {
              setCurrentText(e.target.value);
              if (disposition !== "edited") {
                handleDisposition("edited");
              }
            }}
            placeholder="Suggested response draft..."
          />
        </div>

        {/* Action Row */}
        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-1.5 flex-wrap">
            {citations.length > 0 && (
              <div className="flex items-center gap-1">
                <span className="text-[10px] font-mono text-slate-400">Cited:</span>
                {citations.map((cId) => (
                  <button
                    key={cId}
                    onClick={() => onCitationClick?.(cId)}
                    className="inline-flex items-center gap-1 text-[9px] font-mono bg-slate-950 hover:bg-slate-850 text-indigo-300 border border-slate-800 hover:border-indigo-500/40 px-1.5 py-0.5 rounded transition cursor-pointer"
                  >
                    <span>{cId}</span>
                    <ExternalLink className="h-2 w-2 text-slate-400" />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-1.5">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-[11px] px-2 text-slate-300 hover:text-white hover:bg-slate-800"
              onClick={handleCopy}
            >
              {isCopied ? (
                <>
                  <Check className="h-3 w-3 text-emerald-400 mr-1" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  <span>Copy</span>
                </>
              )}
            </Button>
            <Button
              variant="default"
              size="sm"
              className="h-7 text-[11px] px-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-sm shadow-indigo-600/30"
              onClick={handleInsert}
            >
              <SendHorizontal className="h-3 w-3 mr-1.5" />
              Use Suggestion
            </Button>
          </div>
        </div>
      </div>

      {/* HITL Feedback & Compliance Audit Footer */}
      <div className="py-2 px-4 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-[11px] text-slate-400">
        <span className="text-[10px] font-mono text-slate-500">HITL Audit:</span>
        <div className="flex items-center space-x-1.5">
          <Button
            variant={disposition === "accepted" ? "emerald" : "ghost"}
            size="sm"
            className={`h-6 px-2 text-[10px] font-mono ${
              disposition === "accepted"
                ? "bg-emerald-600 text-white hover:bg-emerald-500"
                : "text-slate-400 hover:text-white"
            }`}
            onClick={() => handleDisposition("accepted")}
          >
            <ThumbsUp className="h-2.5 w-2.5 mr-1" /> Accept
          </Button>
          <Button
            variant={disposition === "edited" ? "secondary" : "ghost"}
            size="sm"
            className={`h-6 px-2 text-[10px] font-mono ${
              disposition === "edited"
                ? "bg-blue-600 text-white hover:bg-blue-500"
                : "text-slate-400 hover:text-white"
            }`}
            onClick={() => handleDisposition("edited")}
          >
            <Edit3 className="h-2.5 w-2.5 mr-1" /> Edited
          </Button>
          <Button
            variant={disposition === "dismissed" ? "destructive" : "ghost"}
            size="sm"
            className={`h-6 px-2 text-[10px] font-mono ${
              disposition === "dismissed"
                ? "bg-rose-600 text-white hover:bg-rose-500"
                : "text-slate-400 hover:text-white"
            }`}
            onClick={() => handleDisposition("dismissed")}
          >
            <ThumbsDown className="h-2.5 w-2.5 mr-1" /> Dismiss
          </Button>
        </div>
      </div>
    </div>
  );
}
