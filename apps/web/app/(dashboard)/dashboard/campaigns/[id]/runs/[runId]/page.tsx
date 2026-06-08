"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Card } from "@/components/ui/input";
import type { AgentLog, AgentRunDetail, Paginated } from "@/types/api";

export default function RunDetailPage() {
  const { runId } = useParams<{ id: string; runId: string }>();

  const { data: run } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => apiFetch<AgentRunDetail>(`/runs/${runId}`),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status && ["queued", "running"].includes(status) ? 3000 : false;
    },
  });

  const { data: logs } = useQuery({
    queryKey: ["run-logs", runId],
    queryFn: () => apiFetch<Paginated<AgentLog>>(`/runs/${runId}/logs`),
    refetchInterval: run?.status === "running" ? 3000 : false,
  });

  if (!run) return <p className="text-muted">Loading...</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold capitalize">Run · {run.status.replace("_", " ")}</h1>
      <p className="mt-1 text-muted">Current step: {run.current_step || "—"}</p>
      {run.error && <p className="mt-2 text-sm text-red-600">{run.error}</p>}

      <div className="mt-8">
        <h2 className="text-lg font-medium">Steps</h2>
        <div className="mt-4 space-y-2">
          {run.steps.map((step) => (
            <Card key={step.id} className="flex items-center justify-between py-4">
              <div>
                <p className="font-medium">{step.step_name}</p>
                <p className="text-sm capitalize text-muted">{step.status}</p>
              </div>
              {step.duration_ms != null && (
                <p className="text-sm text-muted">{step.duration_ms}ms</p>
              )}
            </Card>
          ))}
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-medium">Logs</h2>
        <div className="mt-4 space-y-1 font-mono text-sm">
          {(logs?.data ?? []).map((log) => (
            <div key={log.id} className="rounded border border-border px-3 py-2">
              <span className="text-muted">[{log.level}]</span> {log.message}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
