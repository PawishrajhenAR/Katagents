"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { WORKFLOW_STEPS } from "@/lib/agent-steps";
import { cn } from "@/lib/utils";

interface ProcessGuideProps {
  activeStep?: number;
  className?: string;
  compact?: boolean;
}

export function ProcessGuide({ activeStep = 1, className, compact }: ProcessGuideProps) {
  return (
    <div className={cn("rounded-2xl border border-border bg-card p-5 shadow-sm", className)}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">How it works</p>
          {!compact && (
            <p className="mt-1 text-sm text-muted">Four steps from blank slate to sent emails.</p>
          )}
        </div>
        <Link href="/dashboard/campaigns/new" className="hidden items-center gap-1 text-sm font-medium text-primary hover:underline sm:inline-flex">
          Start now <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      <ol className={cn("grid gap-3", compact ? "grid-cols-2 lg:grid-cols-4" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4")}>
        {WORKFLOW_STEPS.map(({ step, title, hint }) => {
          const isActive = step === activeStep;
          const isDone = step < activeStep;

          return (
            <li
              key={step}
              className={cn(
                "relative rounded-xl border p-4 transition-all duration-300",
                isActive && "border-primary/40 bg-primary/5 shadow-sm",
                isDone && "border-emerald-200 bg-emerald-50/50",
                !isActive && !isDone && "border-border bg-background/50",
              )}
            >
              <div className="flex items-start gap-3">
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold",
                    isActive && "bg-primary text-white",
                    isDone && "bg-emerald-500 text-white",
                    !isActive && !isDone && "bg-border text-muted",
                  )}
                >
                  {isDone ? "✓" : step}
                </span>
                <div>
                  <p className="text-sm font-semibold">{title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted">{hint}</p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
