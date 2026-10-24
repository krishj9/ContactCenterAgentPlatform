import * as React from "react";
import {
  ShieldCheck,
  AlertTriangle,
  SearchX,
  ShieldAlert,
  CheckCircle2,
  Circle,
  ExternalLink,
  Info,
} from "lucide-react";
import type { GroundingStatus } from "@/types/contracts";

export interface ActionStepItem {
  id?: string;
  step_number?: number;
  text: string;
  action_type?: "verify" | "inform" | "escalate" | string;
  citation_ids?: string[];
  completed?: boolean;
}

export interface NextBestActionCardProps {
  actionId?: string;
  title: string;
  description: string;
  actionType?: "verify" | "inform" | "escalate" | "GUIDANCE" | "PROCEDURAL" | "COMPLIANCE" | "ESCALATION" | string;
  steps: (string | ActionStepItem)[];
  groundingState: GroundingStatus;
  citations: string[];
  isFallback?: boolean;
  onCitationClick?: (citationId: string) => void;
  onStepToggle?: (index: number, completed: boolean) => void;
  className?: string;
}

export function NextBestActionCard({
  title,
  description,
  actionType = "procedural",
  steps,
  groundingState,
  citations = [],
  isFallback = false,
  onCitationClick,
  onStepToggle,
  className = "",
}: NextBestActionCardProps) {
  // Normalize steps to objects
  const initialSteps: ActionStepItem[] = React.useMemo(() => {
    return steps.map((s, idx) => {
      if (typeof s === "string") {
        // Simple heuristic to extract action type if prefixed
        let detectedType = "inform";
        let cleanText = s;
        if (/^step\s*\d+:\s*(verify|confirm|authenticate)/i.test(s) || /^(verify|confirm|authenticate)/i.test(s)) {
          detectedType = "verify";
        } else if (/^step\s*\d+:\s*(escalate|transfer|flag)/i.test(s) || /^(escalate|transfer|flag)/i.test(s)) {
          detectedType = "escalate";
        }
        return {
          id: `step-${idx}`,
          step_number: idx + 1,
          text: cleanText,
          action_type: detectedType,
          completed: false,
        };
      }
      return {
        ...s,
        id: s.id || `step-${idx}`,
        step_number: s.step_number || idx + 1,
        completed: s.completed ?? false,
      };
    });
  }, [steps]);

  const [completedSteps, setCompletedSteps] = React.useState<Record<number, boolean>>({});

  const toggleStep = (index: number) => {
    const nextState = !completedSteps[index];
    setCompletedSteps((prev) => ({ ...prev, [index]: nextState }));
    onStepToggle?.(index, nextState);
  };

  const completedCount = Object.values(completedSteps).filter(Boolean).length;
  const progressPercent = initialSteps.length > 0 ? Math.round((completedCount / initialSteps.length) * 100) : 0;

  const getActionTypePill = (type?: string) => {
    const normalized = (type || "").toLowerCase();
    if (normalized.includes("verify") || normalized.includes("compliance")) {
      return {
        label: "VERIFY",
        color: "bg-blue-950/60 text-blue-300 border-blue-500/40",
      };
    }
    if (normalized.includes("escalate") || normalized.includes("escalation")) {
      return {
        label: "ESCALATE",
        color: "bg-amber-950/60 text-amber-300 border-amber-500/40",
      };
    }
    return {
      label: "INFORM",
      color: "bg-cyan-950/60 text-cyan-300 border-cyan-500/40",
    };
  };

  const getGroundingBadge = () => {
    switch (groundingState) {
      case "GROUNDED":
        return {
          icon: <ShieldCheck className="h-3 w-3 text-emerald-400" />,
          label: "GROUNDED",
          classes: "border-emerald-500/40 bg-emerald-950/40 text-emerald-300",
        };
      case "POLICY_REVIEW_NEEDED":
        return {
          icon: <AlertTriangle className="h-3 w-3 text-amber-400" />,
          label: "POLICY REVIEW NEEDED",
          classes: "border-amber-500/40 bg-amber-950/40 text-amber-300",
        };
      case "MISSING_EVIDENCE":
        return {
          icon: <SearchX className="h-3 w-3 text-purple-400" />,
          label: "MISSING EVIDENCE",
          classes: "border-purple-500/40 bg-purple-950/40 text-purple-300",
        };
      case "LOW_CONFIDENCE":
      case "UNGROUNDED":
      default:
        return {
          icon: <ShieldAlert className="h-3 w-3 text-rose-400" />,
          label: "LOW CONFIDENCE",
          classes: "border-rose-500/40 bg-rose-950/40 text-rose-300",
        };
    }
  };

  const groundingBadge = getGroundingBadge();
  const mainTypePill = getActionTypePill(actionType);

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/90 shadow-xl overflow-hidden backdrop-blur-md transition-all duration-300 ${className}`}
    >
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/70 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-white tracking-wide">Next-Best Action</h3>
              <span
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold tracking-wider border flex items-center gap-1 ${groundingBadge.classes}`}
              >
                {groundingBadge.icon}
                {groundingBadge.label}
              </span>
              {isFallback && (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono text-slate-400 bg-slate-800 border border-slate-700">
                  PLAYBOOK FALLBACK
                </span>
              )}
            </div>
          </div>
        </div>

        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${mainTypePill.color}`}
        >
          {mainTypePill.label}
        </span>
      </div>

      {/* Title & Description */}
      <div className="px-4 pt-3.5 pb-2">
        <h4 className="text-sm font-semibold text-slate-100">{title}</h4>
        <p className="text-xs text-slate-300 mt-1 leading-relaxed">{description}</p>

        {/* Progress bar */}
        <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono mb-1.5">
          <span>Action Checklist</span>
          <span>
            {completedCount}/{initialSteps.length} Completed ({progressPercent}%)
          </span>
        </div>
        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Step Checklist */}
      <div className="px-4 py-2.5 space-y-2">
        {initialSteps.map((step, idx) => {
          const isDone = completedSteps[idx] ?? false;
          const stepPill = getActionTypePill(step.action_type);

          return (
            <div
              key={step.id || idx}
              onClick={() => toggleStep(idx)}
              className={`group flex items-start gap-2.5 p-2 rounded-lg border transition-all duration-200 cursor-pointer ${
                isDone
                  ? "bg-slate-950/30 border-slate-800/50 text-slate-400"
                  : "bg-slate-800/40 hover:bg-slate-800/70 border-slate-700/60 text-slate-200"
              }`}
            >
              <button
                type="button"
                className="mt-0.5 shrink-0 transition-transform active:scale-95 text-slate-400 hover:text-white"
                aria-label={`Toggle step ${idx + 1}`}
              >
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <Circle className="h-4 w-4 text-slate-500 group-hover:text-blue-400 transition" />
                )}
              </button>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span
                    className={`font-mono text-[10px] font-bold ${
                      isDone ? "text-slate-500" : "text-blue-400"
                    }`}
                  >
                    STEP {step.step_number || idx + 1}
                  </span>
                  <span
                    className={`px-1 py-0.2 rounded text-[8px] font-mono uppercase border ${stepPill.color}`}
                  >
                    {stepPill.label}
                  </span>
                </div>
                <p
                  className={`text-xs leading-relaxed transition ${
                    isDone ? "line-through text-slate-500" : "text-slate-200 font-normal"
                  }`}
                >
                  {step.text}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Citations Footer */}
      {citations.length > 0 && (
        <div className="px-4 py-2.5 bg-slate-950/50 border-t border-slate-800/70 flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1">
              <Info className="h-3 w-3 text-slate-500" /> Verified Policy Lineage:
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {citations.length} cited chunk{citations.length > 1 ? "s" : ""}
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {citations.map((cId) => (
              <button
                key={cId}
                onClick={() => onCitationClick?.(cId)}
                className="inline-flex items-center gap-1 text-[10px] font-mono bg-slate-900 hover:bg-slate-800 text-blue-300 hover:text-blue-200 border border-slate-700/80 hover:border-blue-500/50 px-2 py-0.5 rounded transition cursor-pointer"
                title={`Inspect evidence for ${cId}`}
              >
                <span>{cId}</span>
                <ExternalLink className="h-2.5 w-2.5 text-slate-400" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
