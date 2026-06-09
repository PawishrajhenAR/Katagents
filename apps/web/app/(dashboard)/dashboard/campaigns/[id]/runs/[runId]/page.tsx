"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Terminal } from "lucide-react";
import { AgentPipeline } from "@/components/agents/agent-pipeline";
import { RunStatusBadge } from "@/components/agents/run-status-badge";
import { Card } from "@/components/ui/input";
import { getStepMeta } from "@/lib/agent-steps";
import { apiFetch } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { AgentLog, AgentRunDetail, Paginated } from "@/types/api";

export default function RunDetailPage() {
  const { id, runId } = useParams<{ id: string; runId: string }>();

  const { data: run } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => apiFetch<AgentRunDetail>(`/runs/${runId}`),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status && ["queued", "running", "waiting_approval"].includes(status) ? 2500 : false;
    },
  });

  const { data: logs } = useQuery({
    queryKey: ["run-logs", runId],
    queryFn: () => apiFetch<Paginated<AgentLog>>(`/runs/${runId}/logs`),
    refetchInterval: run && ["queued", "running", "waiting_approval"].includes(run.status) ? 2500 : false,
  });

  const isLive = run && ["queued", "running", "waiting_approval"].includes(run.status);
  const currentMeta = getStepMeta(run?.current_step);

  if (!run) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <span className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="w-full min-w-0 space-y-8">
      <Link
        href={`/dashboard/campaigns/${id}`}
        className="inline-flex items-center gap-1 text-sm text-muted hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Back to campaign
      </Link>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-display text-3xl font-semibold">Agent run</h1>
            <RunStatusBadge status={run.status} pulse={!!isLive} />
          </div>
          {currentMeta && (
            <p className="mt-2 text-muted">
              {isLive ? "Working on:" : "Last step:"}{" "}
              <span className="font-medium text-foreground">{currentMeta.label}</span>
              <span className="text-muted"> — {currentMeta.description}</span>
            </p>
          )}
          {run.status === "waiting_approval" && (
            <Link
              href={`/dashboard/campaigns/${id}/drafts`}
              className="mt-3 inline-block rounded-lg bg-amber-100 px-3 py-2 text-sm font-medium text-amber-900 hover:bg-amber-200"
            >
              Go approve drafts →
            </Link>
          )}
        </div>
        {isLive && (
          <div className="flex items-center gap-2 rounded-full bg-teal-50 px-4 py-2 text-sm text-teal-800">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-teal-500" />
            </span>
            Live — updating every few seconds
          </div>
        )}
      </div>

      {run.error && (
        <Card className="border-red-200 bg-red-50 text-sm text-red-800">{run.error}</Card>
      )}

      <Card className="overflow-hidden p-0">
        <div className="border-b border-border bg-gradient-to-r from-teal-500/10 to-transparent px-6 py-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">Pipeline progress</p>
        </div>
        <div className="px-4 py-8 sm:px-6">
          <AgentPipeline currentStep={run.current_step} steps={run.steps} />
        </div>
      </Card>

      <section>
        <h2 className="font-display text-lg font-semibold">Step details</h2>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {run.steps.map((step) => {
            const meta = getStepMeta(step.step_name);
            return (
              <Card
                key={step.id}
                className={cn(
                  "py-4 transition-all",
                  step.status === "running" && "border-teal-300 bg-teal-50/50 agent-node-running",
                  step.status === "completed" && "border-emerald-200 bg-emerald-50/30",
                  step.status === "failed" && "border-red-200 bg-red-50/50",
                )}
              >
                <p className="font-medium">{meta?.label ?? step.step_name}</p>
                <p className="mt-1 text-xs text-muted">{meta?.description}</p>
                <div className="mt-3 flex items-center justify-between text-xs">
                  <span className="capitalize text-muted">{step.status}</span>
                  {step.duration_ms != null && <span className="text-muted">{step.duration_ms}ms</span>}
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center gap-2">
          <Terminal className="h-4 w-4 text-muted" />
          <h2 className="font-display text-lg font-semibold">Activity log</h2>
        </div>
        <div className="log-terminal max-h-80 overflow-y-auto rounded-xl border border-slate-800 p-4">
          {(logs?.data ?? []).length === 0 && (
            <p className="text-sm text-slate-500">Waiting for agent output...</p>
          )}
          {(logs?.data ?? []).map((log, i) => (
            <div
              key={log.id}
              className="log-line-enter border-b border-white/5 py-2 text-xs last:border-0"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <span className="text-slate-500">{new Date(log.created_at).toLocaleTimeString()}</span>{" "}
              <span
                className={cn(
                  "font-semibold uppercase",
                  log.level === "error" ? "text-red-400" : log.level === "info" ? "text-teal-400" : "text-slate-400",
                )}
              >
                [{log.level}]
              </span>{" "}
              <span className="text-slate-200">{log.message}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
