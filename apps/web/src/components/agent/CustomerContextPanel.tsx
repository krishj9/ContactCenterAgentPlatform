/**
 * Customer Context & Synthetic CRM History Panel (P6.9).
 *
 * Renders account holder attributes, relationship tenure, Level 3 biometric authentication status,
 * card balances, recent transaction security triggers, and quick action buttons.
 */

import {
  User,
  ShieldCheck,
  CreditCard,
  Calendar,
  AlertCircle,
  ChevronRight,
  DollarSign,
  MapPin,
  Lock,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CustomerContextPayload } from "@/types/contracts";

export interface CustomerContextPanelProps {
  context?: CustomerContextPayload | null;
  onApplyOverride?: () => void;
  onRegisterTravel?: () => void;
  onInspectEvidence?: () => void;
  className?: string;
}

export function CustomerContextPanel({
  context,
  onApplyOverride,
  onRegisterTravel,
  onInspectEvidence,
  className = "",
}: CustomerContextPanelProps) {
  const profile = context || {
    customer_id: "cust_sarah_jenkins_01",
    name: "Sarah Jenkins",
    account_type: "Sapphire Preferred Visa Signature",
    relationship_tier: "Platinum",
    account_number_masked: "•••• •••• •••• 4821",
    context_summary:
      "Customer departed US on Oct 20. Automated security rule triggered on foreign POS terminal (Paris, France - EUR 142.50). No prior travel notice logged.",
  };

  return (
    <div className={`flex flex-col space-y-4 ${className}`}>
      {/* Primary Customer Identity Card */}
      <Card className="bg-slate-900/70 border-slate-800 shadow-md backdrop-blur-sm">
        <CardHeader className="pb-3 border-b border-slate-800/80">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-white">
              <User className="h-4 w-4 text-blue-400" /> Customer Context
            </CardTitle>
            <Badge
              variant="outline"
              className="text-[10px] font-mono border-emerald-500/40 text-emerald-400 bg-emerald-950/20"
            >
              {profile.relationship_tier} Tier
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="pt-4 space-y-3.5 text-xs">
          <div>
            <p className="text-slate-400 text-[11px]">Account Holder</p>
            <p className="font-semibold text-slate-100 text-sm">{profile.name}</p>
          </div>

          <div>
            <p className="text-slate-400 text-[11px] flex items-center gap-1">
              <CreditCard className="h-3 w-3 text-slate-500" /> Primary Product
            </p>
            <p className="font-medium text-slate-200">{profile.account_type}</p>
            <p className="font-mono text-slate-400 text-[11px] mt-0.5">{profile.account_number_masked}</p>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60">
            <div>
              <p className="text-slate-400 text-[11px] flex items-center gap-1">
                <Calendar className="h-3 w-3 text-slate-500" /> Relationship
              </p>
              <p className="font-medium text-slate-200">7 Years (Loyal)</p>
            </div>
            <div>
              <p className="text-slate-400 text-[11px] flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-emerald-400" /> Authentication
              </p>
              <p className="font-medium text-emerald-400 flex items-center gap-1">
                Level 3 Verified
              </p>
            </div>
          </div>

          {/* Balance & Limits */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-[11px]">
            <div>
              <p className="text-slate-400 flex items-center gap-1">
                <DollarSign className="h-3 w-3 text-slate-500" /> Available Credit
              </p>
              <p className="font-mono font-semibold text-slate-100">$18,450.00</p>
            </div>
            <div>
              <p className="text-slate-400">Total Credit Line</p>
              <p className="font-mono text-slate-300">$25,000.00</p>
            </div>
          </div>

          {/* Active Security Context Alert */}
          <div className="pt-2 border-t border-slate-800/60">
            <p className="text-slate-400 text-[11px] mb-1 flex items-center gap-1 font-medium">
              <AlertCircle className="h-3.5 w-3.5 text-amber-400" /> Active Security Event
            </p>
            <div className="text-slate-300 text-[11px] leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 space-y-1">
              <p className="flex items-center gap-1 text-slate-200 font-medium">
                <MapPin className="h-3 w-3 text-rose-400" /> POS Terminal Decline (Paris, France)
              </p>
              <p className="text-slate-400">{profile.context_summary}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Agent Actions Card */}
      <Card className="bg-slate-900/70 border-slate-800 shadow-md flex-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5 text-blue-400" /> Quick Agent Procedures
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <button
            onClick={onApplyOverride}
            className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-blue-500/40 transition flex items-center justify-between cursor-pointer group"
          >
            <div>
              <p className="font-medium text-slate-200 group-hover:text-white">Temporary Geographic Override</p>
              <p className="text-[10px] text-slate-400">Lift 24h foreign terminal decline</p>
            </div>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-blue-400 transition" />
          </button>

          <button
            onClick={onRegisterTravel}
            className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-blue-500/40 transition flex items-center justify-between cursor-pointer group"
          >
            <div>
              <p className="font-medium text-slate-200 group-hover:text-white">Register Travel Notice (30 Days)</p>
              <p className="text-[10px] text-slate-400">France & Schengen Area</p>
            </div>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-blue-400 transition" />
          </button>

          <button
            onClick={onInspectEvidence}
            className="w-full text-left p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-indigo-500/40 transition flex items-center justify-between cursor-pointer group"
          >
            <div>
              <p className="font-medium text-slate-200 group-hover:text-white">Inspect Compliance Policy</p>
              <p className="text-[10px] text-slate-400">View card authorization rules</p>
            </div>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-indigo-400 transition" />
          </button>
        </CardContent>
      </Card>
    </div>
  );
}
