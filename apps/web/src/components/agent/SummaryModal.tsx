import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Clock,
  Sparkles,
  Save,
} from "lucide-react";

export interface SummaryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  summary?: {
    call_overview: string;
    key_issues: string[];
    actions_completed: string[];
    required_followups: string[];
    crm_case_note: string;
  } | null;
  sessionId?: string;
  onSaveToCrm?: (note: string) => void;
}

export function SummaryModal({
  open,
  onOpenChange,
  summary,
  sessionId = "sess_current",
  onSaveToCrm,
}: SummaryModalProps) {
  const [editedNote, setEditedNote] = React.useState(summary?.crm_case_note || "");
  const [copied, setCopied] = React.useState(false);
  const [saved, setSaved] = React.useState(false);

  React.useEffect(() => {
    if (summary?.crm_case_note) {
      setEditedNote(summary.crm_case_note);
    }
  }, [summary]);

  const handleCopy = () => {
    navigator.clipboard.writeText(editedNote);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
    onSaveToCrm?.(editedNote);
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onOpenChange(false);
    }, 1200);
  };

  const data = summary || {
    call_overview:
      "Customer called from Paris regarding a POS transaction decline. Agent verified cardholder identity, confirmed lack of previous travel notices, and applied temporary geographic security override.",
    key_issues: ["Automated fraud prevention hold triggered in foreign jurisdiction", "No prior travel notification filed"],
    actions_completed: [
      "Level 3 cardholder identity authentication verified",
      "Temporary 24h geographic decline override lifted for card terminal 4821",
      "Registered 30-day travel authorization for France and Schengen region",
    ],
    required_followups: ["Monitor transaction authorizations over next 24 hours"],
    crm_case_note: `[CRM DISPOSITION NOTE]\nSession: ${sessionId}\nCaller: Sarah Jenkins (Platinum)\nIssue: POS Foreign Transaction Decline (Paris, France)\nResolution: Verified identity. Temporary override applied to security hold. Registered 30-day travel notice.\nFollow-up: None required from customer. System monitoring active.`,
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-800 text-slate-100 p-0 overflow-hidden shadow-2xl">
        {/* Header */}
        <DialogHeader className="p-5 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <FileText className="h-4 w-4" />
              </div>
              <div>
                <DialogTitle className="text-base font-semibold text-white flex items-center gap-2">
                  Post-Call CRM Summary & Wrap-up
                  <Badge variant="outline" className="text-[10px] border-emerald-500/40 text-emerald-400 bg-emerald-950/30">
                    Ready for Disposition
                  </Badge>
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-400">
                  Synthesized from real-time customer and agent transcript turns
                </DialogDescription>
              </div>
            </div>
          </div>
        </DialogHeader>

        {/* Body Content */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Overview */}
          <div className="space-y-1">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
              Call Overview
            </h4>
            <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              {data.call_overview}
            </p>
          </div>

          {/* Key Issues & Actions Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Key Issues */}
            <div className="space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
              <h5 className="text-[11px] font-semibold text-amber-300 flex items-center gap-1 font-mono uppercase">
                <AlertCircle className="h-3 w-3 text-amber-400" /> Key Issues Discussed
              </h5>
              <ul className="space-y-1 text-xs text-slate-300">
                {data.key_issues.map((issue, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 leading-snug">
                    <span className="text-slate-500">•</span>
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Actions Completed */}
            <div className="space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
              <h5 className="text-[11px] font-semibold text-emerald-300 flex items-center gap-1 font-mono uppercase">
                <CheckCircle2 className="h-3 w-3 text-emerald-400" /> Actions Executed
              </h5>
              <ul className="space-y-1 text-xs text-slate-300">
                {data.actions_completed.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 leading-snug">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Required Follow-ups */}
          {data.required_followups && data.required_followups.length > 0 && (
            <div className="space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
              <h5 className="text-[11px] font-semibold text-blue-300 flex items-center gap-1 font-mono uppercase">
                <Clock className="h-3 w-3 text-blue-400" /> Required Follow-ups
              </h5>
              <ul className="space-y-1 text-xs text-slate-300">
                {data.required_followups.map((fu, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 leading-snug">
                    <span className="text-blue-400">→</span>
                    <span>{fu}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* CRM Case Note (Editable) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                CRM Case Note Draft (Editable)
              </h4>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white transition cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" />
                    <span>Copy note</span>
                  </>
                )}
              </button>
            </div>
            <textarea
              className="w-full h-32 rounded-lg bg-slate-950 border border-slate-700/80 p-3 text-xs text-slate-200 font-mono leading-relaxed resize-none focus:outline-none focus:border-emerald-500"
              value={editedNote}
              onChange={(e) => setEditedNote(e.target.value)}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="text-xs text-slate-400 hover:text-white"
          >
            Close
          </Button>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="text-xs border-slate-700 hover:bg-slate-800"
            >
              {copied ? <Check className="h-3.5 w-3.5 mr-1 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 mr-1" />}
              {copied ? "Copied Note" : "Copy to Clipboard"}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSave}
              className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              {saved ? (
                <>
                  <Check className="h-3.5 w-3.5 mr-1" /> Case Synced
                </>
              ) : (
                <>
                  <Save className="h-3.5 w-3.5 mr-1" /> Save & Disposition
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
