import {
  ShieldCheck,
  AlertTriangle,
  SearchX,
  ShieldAlert,
  ExternalLink,
} from "lucide-react";
import type { GroundingStatus } from "@/types/contracts";

export interface GroundingBannerProps {
  state: GroundingStatus;
  warningCode?: string | null;
  warningMessage?: string | null;
  onInspectEvidence?: () => void;
  className?: string;
}

export function GroundingBanner({
  state,
  warningCode,
  warningMessage,
  onInspectEvidence,
  className = "",
}: GroundingBannerProps) {
  const getBannerConfig = () => {
    switch (state) {
      case "GROUNDED":
        return {
          icon: <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-400" />,
          title: "Policy Grounded & Verified",
          description:
            "Recommended actions strictly cite active, verified operational compliance policies.",
          borderColor: "border-emerald-500/40",
          bgColor: "bg-emerald-950/30",
          textColor: "text-emerald-300",
          badgeBg: "bg-emerald-900/40 border-emerald-500/50 text-emerald-300",
          label: "GROUNDED",
        };
      case "POLICY_REVIEW_NEEDED":
        return {
          icon: <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />,
          title: "Policy Review Needed",
          description:
            warningMessage ||
            "Operational procedures lack direct policy evidence (score < τ_policy). Restricted to general advice.",
          borderColor: "border-amber-500/40",
          bgColor: "bg-amber-950/30",
          textColor: "text-amber-300",
          badgeBg: "bg-amber-900/40 border-amber-500/50 text-amber-300",
          label: "POLICY REVIEW NEEDED",
        };
      case "MISSING_EVIDENCE":
        return {
          icon: <SearchX className="h-4 w-4 shrink-0 text-purple-400" />,
          title: "Missing Authoritative Evidence",
          description:
            warningMessage ||
            "No retrieved chunks exceeded the evidence threshold (τ_evidence). Operational recommendations suppressed.",
          borderColor: "border-purple-500/40",
          bgColor: "bg-purple-950/30",
          textColor: "text-purple-300",
          badgeBg: "bg-purple-900/40 border-purple-500/50 text-purple-300",
          label: "MISSING EVIDENCE",
        };
      case "LOW_CONFIDENCE":
      case "UNGROUNDED":
      default:
        return {
          icon: <ShieldAlert className="h-4 w-4 shrink-0 text-rose-400" />,
          title: "Low Intent Confidence / Out of Scope",
          description:
            warningMessage ||
            "Confidence is below threshold (0.55) or query is out-of-scope. Automated next-best actions disabled.",
          borderColor: "border-rose-500/40",
          bgColor: "bg-rose-950/30",
          textColor: "text-rose-300",
          badgeBg: "bg-rose-900/40 border-rose-500/50 text-rose-300",
          label: "LOW CONFIDENCE",
        };
    }
  };

  const config = getBannerConfig();

  return (
    <div
      className={`flex items-start justify-between gap-3 p-3 rounded-xl border ${config.borderColor} ${config.bgColor} ${config.textColor} text-xs transition-all duration-300 shadow-md ${className}`}
    >
      <div className="flex items-start gap-2.5">
        <div className="mt-0.5">{config.icon}</div>
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-xs text-white">{config.title}</span>
            <span
              className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold uppercase tracking-wider border ${config.badgeBg}`}
            >
              {config.label}
            </span>
            {warningCode && (
              <span className="font-mono text-[10px] text-slate-400">({warningCode})</span>
            )}
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">{config.description}</p>
        </div>
      </div>

      {onInspectEvidence && (
        <button
          onClick={onInspectEvidence}
          className="shrink-0 flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-700/60 text-slate-200 hover:text-white text-[11px] font-medium transition cursor-pointer"
        >
          <span>Evidence</span>
          <ExternalLink className="h-3 w-3 text-slate-400" />
        </button>
      )}
    </div>
  );
}
