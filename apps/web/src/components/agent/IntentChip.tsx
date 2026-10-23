import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  ChevronRight,
  BrainCircuit,
  AlertTriangle,
  HelpCircle,
  Quote,
} from "lucide-react";
import { ExemplarDrawer } from "./ExemplarDrawer";
import type { IntentCandidatePayload } from "@/types/contracts";

export interface IntentChipProps {
  intentLabel: string;
  confidence: number;
  isOutOfScope?: boolean;
  degraded?: boolean;
  triggeredByText?: string;
  candidates?: IntentCandidatePayload[];
  exemplarIds?: string[];
  className?: string;
  onInspect?: () => void;
}

export function IntentChip({
  intentLabel,
  confidence,
  isOutOfScope = false,
  degraded = false,
  triggeredByText = "card was just declined at a restaurant in Paris",
  candidates = [],
  exemplarIds = [],
  className = "",
  onInspect,
}: IntentChipProps) {
  const [isDrawerOpen, setIsDrawerOpen] = React.useState(false);

  const formattedIntent = intentLabel
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  const confidencePercent = (confidence * 100).toFixed(1);

  const handleOpenDrawer = () => {
    setIsDrawerOpen(true);
    if (onInspect) {
      onInspect();
    }
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.7) return "text-emerald-400";
    if (conf >= 0.55) return "text-amber-400";
    return "text-rose-400";
  };

  const getProgressBarGradient = (conf: number) => {
    if (conf >= 0.7) return "from-blue-500 via-indigo-500 to-emerald-400";
    if (conf >= 0.55) return "from-amber-500 to-yellow-400";
    return "from-rose-500 to-red-400";
  };

  return (
    <>
      <Card
        className={`bg-slate-900/80 border-slate-800 shadow-xl hover:border-slate-700/80 transition-all duration-300 relative overflow-hidden group ${className}`}
      >
        {/* Subtle top accent gradient */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-purple-500 via-blue-500 to-emerald-400 opacity-80" />

        <CardHeader className="pb-2.5 pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-6 w-6 rounded-md bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <Sparkles className="h-3.5 w-3.5" />
              </div>
              <CardTitle className="text-xs font-semibold text-white tracking-wide">
                Detected Issue & Intent
              </CardTitle>
            </div>

            {degraded ? (
              <Badge
                variant="outline"
                className="border-amber-500/40 text-amber-300 bg-amber-950/30 text-[10px] font-mono flex items-center gap-1"
              >
                <AlertTriangle className="h-2.5 w-2.5 text-amber-400" />
                k-NN Fallback (Degraded)
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="border-purple-500/40 text-purple-300 bg-purple-950/30 text-[10px] font-mono flex items-center gap-1"
              >
                <BrainCircuit className="h-2.5 w-2.5 text-purple-400" />
                LoRA Gemma 1B Head
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-3 text-xs pt-1">
          {/* Intent Title & Calibrated Confidence */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-slate-100 tracking-tight">
                {formattedIntent}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">({intentLabel})</span>
              {isOutOfScope && (
                <Badge
                  variant="outline"
                  className="border-rose-500/40 text-rose-300 bg-rose-950/40 text-[10px]"
                >
                  Out of Scope
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className={`font-mono font-bold text-xs ${getConfidenceColor(confidence)}`}>
                {confidencePercent}%
              </span>
              <span className="text-[10px] text-slate-400">Confidence</span>
            </div>
          </div>

          {/* Calibrated Confidence Meter Bar */}
          <div className="space-y-1">
            <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
              <div
                className={`h-full bg-gradient-to-r ${getProgressBarGradient(
                  confidence
                )} rounded-full transition-all duration-700 ease-out`}
                style={{ width: `${Math.min(100, Math.max(3, confidence * 100))}%` }}
              />
            </div>
            <div className="flex justify-between text-[9px] text-slate-500 font-mono px-0.5">
              <span>0%</span>
              <span className="text-amber-500/80">τ_oos 55%</span>
              <span className="text-emerald-500/80">Threshold 70%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Trigger Utterance Snippet */}
          {triggeredByText && (
            <div className="flex items-start gap-1.5 text-[11px] text-slate-400 bg-slate-950/40 p-2 rounded-lg border border-slate-800/60">
              <Quote className="h-3 w-3 shrink-0 text-slate-500 mt-0.5" />
              <span className="line-clamp-2 leading-relaxed">
                Triggered by: <span className="text-slate-300 italic">"{triggeredByText}"</span>
              </span>
            </div>
          )}

          {/* Explainability Drawer Button */}
          <div className="pt-1">
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenDrawer}
              className="w-full text-xs h-8 bg-slate-800/40 hover:bg-slate-800 border-slate-700/60 hover:border-purple-500/40 text-slate-200 hover:text-white transition-all flex items-center justify-between group/btn cursor-pointer"
            >
              <span className="flex items-center gap-1.5 font-medium">
                <HelpCircle className="h-3.5 w-3.5 text-purple-400 group-hover/btn:text-purple-300 transition-colors" />
                Why this intent? Inspect 3 Nearest Exemplars
              </span>
              <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover/btn:translate-x-0.5 transition-transform" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Slide-over Explainability Drawer */}
      <ExemplarDrawer
        open={isDrawerOpen}
        onOpenChange={setIsDrawerOpen}
        intentLabel={intentLabel}
        confidence={confidence}
        isOutOfScope={isOutOfScope}
        degraded={degraded}
        candidates={candidates}
        exemplarIds={exemplarIds}
        customerUtterance={triggeredByText}
      />
    </>
  );
}
