import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-blue-600 text-white shadow hover:bg-blue-500",
        secondary:
          "border-transparent bg-slate-800 text-slate-200 hover:bg-slate-700",
        destructive:
          "border-transparent bg-red-600/80 text-white shadow hover:bg-red-500",
        outline: "border-slate-700 text-slate-300",
        // Grounding status badges
        grounded:
          "border-emerald-500/40 bg-emerald-950/60 text-emerald-300 shadow-sm shadow-emerald-950",
        policy_review_needed:
          "border-amber-500/40 bg-amber-950/60 text-amber-300 shadow-sm shadow-amber-950",
        missing_evidence:
          "border-purple-500/40 bg-purple-950/60 text-purple-300 shadow-sm shadow-purple-950",
        ungrounded:
          "border-rose-500/40 bg-rose-950/60 text-rose-300 shadow-sm shadow-rose-950",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
