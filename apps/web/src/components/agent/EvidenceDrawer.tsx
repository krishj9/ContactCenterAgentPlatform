import * as React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Search,
  Copy,
  Check,
  ExternalLink,
  Layers,
} from "lucide-react";
import type { EvidenceItemPayload, GroundingStatus } from "@/types/contracts";

export interface EvidenceDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  evidence: EvidenceItemPayload[];
  selectedCitationId?: string | null;
  groundingState?: GroundingStatus;
}

export function EvidenceDrawer({
  open,
  onOpenChange,
  evidence = [],
  selectedCitationId,
  groundingState = "GROUNDED",
}: EvidenceDrawerProps) {
  const [filterType, setFilterType] = React.useState<"all" | "policy" | "faq">("all");
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const filteredEvidence = React.useMemo(() => {
    if (filterType === "all") return evidence;
    return evidence.filter((e) => e.store_type === filterType);
  }, [evidence, filterType]);

  const handleCopyChunk = (chunk: EvidenceItemPayload) => {
    navigator.clipboard.writeText(`${chunk.chunk_id}\n\n${chunk.title}\n${chunk.snippet}`);
    setCopiedId(chunk.chunk_id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.68) return "bg-emerald-500 text-emerald-400";
    if (score >= 0.48) return "bg-amber-500 text-amber-400";
    return "bg-rose-500 text-rose-400";
  };

  const policyCount = evidence.filter((e) => e.store_type === "policy").length;
  const faqCount = evidence.filter((e) => e.store_type === "faq").length;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl bg-slate-900 border-l border-slate-800 text-slate-100 flex flex-col p-0 overflow-hidden"
      >
        {/* Header */}
        <SheetHeader className="p-5 border-b border-slate-800/80 bg-slate-900/90 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Layers className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <SheetTitle className="text-base font-semibold text-white">
                    Retrieval Evidence & Lineage
                  </SheetTitle>
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase border border-indigo-500/40 bg-indigo-950/40 text-indigo-300">
                    {groundingState}
                  </span>
                </div>
                <SheetDescription className="text-xs text-slate-400">
                  Authoritative Policy and FAQ chunks retrieved via hybrid search + reranking
                </SheetDescription>
              </div>
            </div>
          </div>

          {/* Filtering Tabs & Threshold Metrics */}
          <div className="mt-4 flex items-center justify-between gap-2 pt-2 border-t border-slate-800/60">
            <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setFilterType("all")}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition cursor-pointer ${
                  filterType === "all"
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                All ({evidence.length})
              </button>
              <button
                onClick={() => setFilterType("policy")}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition cursor-pointer ${
                  filterType === "policy"
                    ? "bg-blue-600/30 text-blue-300 border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Policy ({policyCount})
              </button>
              <button
                onClick={() => setFilterType("faq")}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition cursor-pointer ${
                  filterType === "faq"
                    ? "bg-purple-600/30 text-purple-300 border border-purple-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                FAQ ({faqCount})
              </button>
            </div>

            <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
              <span className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                τ_pol: 0.68
              </span>
              <span className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                τ_evid: 0.48
              </span>
            </div>
          </div>
        </SheetHeader>

        {/* Evidence List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {filteredEvidence.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs space-y-2">
              <Search className="h-8 w-8 mx-auto text-slate-600" />
              <p>No matching evidence items found in this store filter.</p>
            </div>
          ) : (
            filteredEvidence.map((item) => {
              const isSelected = selectedCitationId && item.chunk_id.toLowerCase().includes(selectedCitationId.toLowerCase());
              const scorePercent = Math.min(100, Math.round(item.similarity_score * 100));
              const scoreColorClass = getScoreColor(item.similarity_score);

              return (
                <div
                  key={item.chunk_id}
                  className={`rounded-xl border transition-all duration-300 overflow-hidden ${
                    isSelected
                      ? "border-blue-500 bg-blue-950/20 shadow-lg shadow-blue-500/10 ring-1 ring-blue-500/40"
                      : "border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-950/80"
                  }`}
                >
                  {/* Card Header */}
                  <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase tracking-wider border ${
                            item.store_type === "policy"
                              ? "bg-blue-950/80 text-blue-300 border-blue-500/40"
                              : "bg-purple-950/80 text-purple-300 border-purple-500/40"
                          }`}
                        >
                          {item.store_type}
                        </span>
                        <span className="font-mono text-xs font-semibold text-slate-200">
                          {item.chunk_id}
                        </span>
                        {item.risk_level && (
                          <span
                            className={`px-1.5 py-0.2 rounded text-[8px] font-mono uppercase border ${
                              item.risk_level.toUpperCase() === "HIGH"
                                ? "bg-rose-950 text-rose-300 border-rose-500/40"
                                : item.risk_level.toUpperCase() === "MEDIUM"
                                ? "bg-amber-950 text-amber-300 border-amber-500/40"
                                : "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                            }`}
                          >
                            {item.risk_level} RISK
                          </span>
                        )}
                      </div>
                      <h4 className="text-xs font-medium text-slate-100">{item.title}</h4>
                    </div>

                    <button
                      onClick={() => handleCopyChunk(item)}
                      className="shrink-0 p-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-slate-400 hover:text-white transition cursor-pointer"
                      title="Copy chunk ID and text"
                    >
                      {copiedId === item.chunk_id ? (
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Similarity Score Meter */}
                  <div className="px-3.5 py-2 bg-slate-900/30 border-b border-slate-800/40 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-400">Rerank Cross-Encoder Score:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${scoreColorClass.split(" ")[0]}`}
                          style={{ width: `${scorePercent}%` }}
                        />
                      </div>
                      <span className={`font-semibold ${scoreColorClass.split(" ")[1]}`}>
                        {item.similarity_score.toFixed(3)}
                      </span>
                    </div>
                  </div>

                  {/* Verbatim Snippet */}
                  <div className="p-3.5 text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line bg-slate-950/20">
                    {item.snippet}
                  </div>

                  {/* Footer with source link if available */}
                  {item.source_uri && (
                    <div className="px-3.5 py-2 border-t border-slate-800/60 bg-slate-900/40 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                      <span className="truncate max-w-[320px]">Source: {item.source_uri}</span>
                      <a
                        href={item.source_uri}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition"
                      >
                        <span>View doc</span>
                        <ExternalLink className="h-2.5 w-2.5" />
                      </a>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
