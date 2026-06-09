"use client";

import { Fragment } from "react";
import { Check, Loader2 } from "lucide-react";
import { EMAIL_OUTREACH_STEPS, getStepMeta } from "@/lib/agent-steps";
import { cn } from "@/lib/utils";

type StepState = "pending" | "running" | "completed" | "failed" | "waiting";
type ConnectorState = "idle" | "complete" | "active";

interface AgentPipelineProps {
  currentStep?: string | null;
  steps?: { step_name: string; status: string }[];
  compact?: boolean;
  className?: string;
}

function resolveStepState(
  stepId: string,
  currentStep: string | null | undefined,
  steps?: { step_name: string; status: string }[],
): StepState {
  const row = steps?.find((s) => s.step_name === stepId);
  if (row?.status === "failed") return "failed";
  if (row?.status === "completed") return "completed";
  if (row?.status === "running" || stepId === currentStep) {
    if (stepId === "approval" && currentStep === "approval") return "waiting";
    return "running";
  }
  const currentIdx = EMAIL_OUTREACH_STEPS.findIndex((s) => s.id === currentStep);
  const stepIdx = EMAIL_OUTREACH_STEPS.findIndex((s) => s.id === stepId);
  if (currentIdx >= 0 && stepIdx < currentIdx) return "completed";
  return "pending";
}

function resolveConnectorState(
  leftStepId: string,
  rightStepId: string,
  currentStep: string | null | undefined,
  steps?: { step_name: string; status: string }[],
): ConnectorState {
  const left = resolveStepState(leftStepId, currentStep, steps);
  const right = resolveStepState(rightStepId, currentStep, steps);

  if (left === "failed") return "idle";
  if (left === "running") return "active";
  if (left === "completed") {
    if (right === "running" || right === "waiting") return "active";
    if (right === "completed" || right === "failed") return "complete";
    return "complete";
  }
  return "idle";
}

function PipelineConnector({ state }: { state: ConnectorState }) {
  return (
    <div className="pipeline-track relative h-0.5 w-full" aria-hidden>
      <div
        className={cn(
          "pipeline-track-fill absolute inset-y-0 left-0 rounded-full",
          state === "idle" && "w-0 opacity-0",
          state === "complete" && "w-full bg-emerald-400 opacity-100",
          state === "active" && "w-full pipeline-track-flow opacity-100",
        )}
      />
    </div>
  );
}

export function AgentPipeline({ currentStep, steps, compact, className }: AgentPipelineProps) {
  return (
    <div className={cn("w-full min-w-0", className)}>
      <div className="flex w-full min-w-0 items-start">
        {EMAIL_OUTREACH_STEPS.map((step, index) => {
          const state = resolveStepState(step.id, currentStep, steps);
          const Icon = step.icon;
          const meta = getStepMeta(step.id)!;
          const nextStep = EMAIL_OUTREACH_STEPS[index + 1];
          const connectorState = nextStep
            ? resolveConnectorState(step.id, nextStep.id, currentStep, steps)
            : null;

          return (
            <Fragment key={step.id}>
              <div
                className={cn(
                  "flex shrink-0 flex-col items-center text-center",
                  compact ? "w-[4.25rem] sm:w-[4.75rem]" : "w-[5.25rem] sm:w-[6rem] lg:w-[7rem]",
                )}
              >
                <div
                  className={cn(
                    "relative z-10 flex h-10 w-10 items-center justify-center rounded-xl border-2 transition-colors duration-300",
                    state === "pending" && "border-border bg-card text-muted",
                    state === "running" && "border-teal-500 bg-teal-500 text-white",
                    state === "waiting" && "border-amber-400 bg-amber-50 text-amber-700",
                    state === "completed" && "border-emerald-400 bg-emerald-500 text-white",
                    state === "failed" && "border-red-400 bg-red-50 text-red-600",
                  )}
                >
                  {state === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : state === "completed" ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </div>

                <p
                  className={cn(
                    "mt-2 text-xs font-semibold leading-tight",
                    state === "pending" ? "text-muted" : "text-foreground",
                  )}
                >
                  {compact ? meta.shortLabel : meta.label}
                </p>
                {!compact && (
                  <p className="mt-1 hidden px-0.5 text-[11px] leading-snug text-muted lg:block">
                    {meta.description}
                  </p>
                )}
              </div>

              {connectorState && (
                <div
                  className={cn(
                    "flex shrink-0 items-center self-start pt-5",
                    compact ? "w-3 sm:w-4" : "min-w-[0.75rem] flex-1",
                  )}
                  aria-hidden
                >
                  <PipelineConnector state={connectorState} />
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
