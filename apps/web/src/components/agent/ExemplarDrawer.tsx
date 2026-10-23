import * as React from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import {
  BrainCircuit,
  Cpu,
  BookOpen,
  Quote,
  ShieldAlert,
  Sliders,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { getExemplarsForIntent, type TrainingExemplar } from "@/lib/exemplars";
import type { IntentCandidatePayload } from "@/types/contracts";

export interface ExemplarDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  intentLabel: string;
  confidence: number;
  isOutOfScope?: boolean;
  degraded?: boolean;
  candidates?: IntentCandidatePayload[];
  exemplarIds?: string[];
  customerUtterance?: string;
  modelVersion?: string;
  taxonomyVersion?: string;
}

export function ExemplarDrawer({
  open,
  onOpenChange,
  intentLabel,
  confidence,
  isOutOfScope = false,
  degraded = false,
  candidates = [],
  exemplarIds = [],
  customerUtterance = "Customer turn speech transcript",
  modelVersion = "intent-gemma3-1b-lora@2026-10-23",
  taxonomyVersion = "tx-14",
}: ExemplarDrawerProps) {
  const exemplars: TrainingExemplar[] = React.useMemo(() => {
    return getExemplarsForIntent(intentLabel, exemplarIds);
  }, [intentLabel, exemplarIds]);

  // Fallback candidate distribution if none provided
  const displayCandidates: IntentCandidatePayload[] = React.useMemo(() => {
    if (candidates && candidates.length > 0) {
      return candidates;
    }
    return [
      { intent_label: intentLabel, confidence },
      {
        intent_label: intentLabel === "card_declined" ? "country_support" : "card_declined",
        confidence: Math.max(0.02, Number(((1 - confidence) * 0.7).toFixed(3))),
      },
      {
        intent_label: "general_inquiry",
        confidence: Math.max(0.01, Number(((1 - confidence) * 0.3).toFixed(3))),
      },
    ];
  }, [candidates, intentLabel, confidence]);

  const formattedIntent = intentLabel.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const confidencePercent = (confidence * 100).toFixed(1);

  // Check multi-issue condition (Spec §3.2.1: p2 >= 0.25 and p1 - p2 < 0.30)
  const isMultiIssue =
    displayCandidates.length > 1 &&
    displayCandidates[1].confidence >= 0.25 &&
    displayCandidates[0].confidence - displayCandidates[1].confidence < 0.3;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl bg-[#090d19]/95 text-slate-100 border-l border-slate-800/80 backdrop-blur-2xl p-0 overflow-y-auto z-50 flex flex-col shadow-2xl"
      >
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800/80 bg-slate-900/40">
          <SheetHeader className="text-left space-y-1">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <BrainCircuit className="h-4 w-4" />
              </div>
              <SheetTitle className="text-base font-semibold text-white tracking-tight">
                Intent Explainability & Provenance
              </SheetTitle>
            </div>
            <SheetDescription className="text-xs text-slate-400 leading-relaxed pt-1">
              Detailed machine learning explainability breakdown: nearest training exemplars,
              calibrated confidence distribution, and serving runtime lineage.
            </SheetDescription>
          </SheetHeader>

          {/* Current Decision Summary Pill */}
          <div className="mt-4 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-sm font-semibold text-white">
                {formattedIntent}
              </span>
              {degraded && (
                <Badge
                  variant="outline"
                  className="border-amber-500/40 text-amber-300 bg-amber-950/30 text-[10px]"
                >
                  k-NN Fallback (Degraded)
                </Badge>
              )}
              {isOutOfScope && (
                <Badge
                  variant="outline"
                  className="border-rose-500/40 text-rose-300 bg-rose-950/30 text-[10px]"
                >
                  Out of Scope
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-slate-400">Calibrated:</span>
              <span
                className={`font-mono text-xs font-bold ${
                  confidence >= 0.7
                    ? "text-emerald-400"
                    : confidence >= 0.55
                    ? "text-amber-400"
                    : "text-rose-400"
                }`}
              >
                {confidencePercent}%
              </span>
            </div>
          </div>
        </div>

        {/* Drawer Scrollable Body */}
        <div className="p-6 space-y-6 flex-1 text-xs">
          {/* Section: Triggering Customer Speech */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-slate-300 font-medium">
              <Quote className="h-3.5 w-3.5 text-blue-400" />
              <span>Customer Utterance Context</span>
            </div>
            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800/70 text-slate-200 text-xs italic leading-relaxed">
              "{customerUtterance}"
            </div>
          </div>

          {/* Section: Model & Runtime Telemetry (Spec §3.2) */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-slate-300 font-medium">
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
              <span>Model & Serving Specifications</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Model Architecture
                </span>
                <span className="font-mono text-[11px] text-slate-200 font-medium mt-0.5 block">
                  Gemma 3 1B LoRA (r=16, α=32)
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Serving Engine
                </span>
                <span className="font-mono text-[11px] text-slate-200 font-medium mt-0.5 block flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                  {degraded ? "k-NN Fallback (CPU)" : "ONNX Runtime int8 CPU (<100ms)"}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Post-Training Calibration
                </span>
                <span className="font-mono text-[11px] text-slate-200 font-medium mt-0.5 block">
                  T = 0.1000 • τ_oos = 0.55 • ECE ≤ 0.05
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Lineage Versions
                </span>
                <span className="font-mono text-[11px] text-slate-200 font-medium mt-0.5 block">
                  {modelVersion} • {taxonomyVersion}
                </span>
              </div>
            </div>
          </div>

          {/* Section: 3 Nearest Training Exemplars (Spec §3.2 Explainability) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                <BookOpen className="h-3.5 w-3.5 text-emerald-400" />
                <span>3 Nearest Training Exemplars</span>
              </div>
              <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-800">
                k-NN Evidence (k=3)
              </Badge>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Utterances from the Banking77 and CLINC150 corpora that exhibit highest cosine
              similarity to the active customer speech turn:
            </p>

            <div className="space-y-2.5">
              {exemplars.slice(0, 3).map((ex, idx) => (
                <div
                  key={ex.id || idx}
                  className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition-all space-y-2 group"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded bg-purple-950/60 border border-purple-500/30 text-purple-300 font-mono text-[10px] font-semibold">
                        #{idx + 1} Neighbor
                      </span>
                      <span className="font-mono text-slate-400 text-[10px]">{ex.id}</span>
                    </div>
                    <div className="flex items-center gap-1 text-emerald-400 font-mono text-[11px]">
                      <span>{(ex.similarity * 100).toFixed(1)}% match</span>
                    </div>
                  </div>

                  <p className="text-slate-200 text-xs leading-relaxed group-hover:text-white transition-colors">
                    "{ex.text}"
                  </p>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-900 text-[10px] text-slate-400 font-mono">
                    <span>Corpus: {ex.corpus}</span>
                    <span className="text-slate-300">Label: {ex.intent}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section: Candidate Softmax Distribution */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                <Sliders className="h-3.5 w-3.5 text-blue-400" />
                <span>Calibrated Candidate Probabilities</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500">Softmax T=0.10</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2.5">
              {displayCandidates.map((cand, idx) => {
                const candPercent = (cand.confidence * 100).toFixed(1);
                return (
                  <div key={cand.intent_label || idx} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-slate-200">
                        {idx + 1}. {cand.intent_label}
                      </span>
                      <span className="font-mono text-slate-300 font-semibold">{candPercent}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          idx === 0
                            ? "bg-gradient-to-r from-blue-500 to-emerald-400"
                            : "bg-slate-700"
                        }`}
                        style={{ width: `${Math.min(100, Math.max(2, cand.confidence * 100))}%` }}
                      />
                    </div>
                  </div>
                );
              })}

              {isMultiIssue && (
                <div className="mt-3 p-2 rounded-lg bg-amber-950/40 border border-amber-500/30 flex items-center gap-2 text-amber-300 text-[11px]">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-400" />
                  <span>
                    <strong>Multi-Issue Detected:</strong> Secondary intent confidence &ge; 25% with
                    margin &lt; 30% (Spec §3.2.1).
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Section: HITL Invariant Notice (Spec §3.2, R14) */}
          <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-500/20 flex items-start gap-2.5 text-blue-300 text-[11px]">
            <ShieldAlert className="h-4 w-4 shrink-0 text-blue-400 mt-0.5" />
            <span className="leading-relaxed">
              <strong>Human-in-the-Loop Assistive Guardrail (R14):</strong> Intent classification
              strictly informs policy retrieval and recommendation cards. Autonomous banking
              executions are disabled by design.
            </span>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
