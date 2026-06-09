"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock } from "lucide-react";
import { RunStatusBadge } from "@/components/agents/run-status-badge";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import { getStepMeta } from "@/lib/agent-steps";
import type { AgentRun, Campaign, Paginated } from "@/types/api";

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: campaign } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => apiFetch<Campaign>(`/campaigns/${id}`),
  });

  const { data: runs } = useQuery({
    queryKey: ["runs", id],
    queryFn: () => apiFetch<Paginated<AgentRun>>(`/campaigns/${id}/runs`),
    refetchInterval: (q) => {
      const active = q.state.data?.data?.some((r) =>
        ["queued", "running", "waiting_approval"].includes(r.status),
      );
      return active ? 4000 : false;
    },
  });

  if (!campaign) return null;

  const nextAction =
    campaign.lead_count === 0
      ? { text: "Add leads to get started", href: `/dashboard/campaigns/${id}/leads` }
      : campaign.pending_drafts > 0
        ? { text: "Review pending drafts", href: `/dashboard/campaigns/${id}/drafts` }
        : { text: "Ready — click Run agent above", href: null };

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="stat-card">
          <p className="text-sm text-muted">Leads in campaign</p>
          <p className="mt-2 font-display text-3xl font-bold">{campaign.lead_count}</p>
          <Link href={`/dashboard/campaigns/${id}/leads`} className="mt-2 inline-block text-xs font-medium text-primary hover:underline">
            Manage leads →
          </Link>
        </Card>
        <Card className="stat-card">
          <p className="text-sm text-muted">Drafts to approve</p>
          <p className="mt-2 font-display text-3xl font-bold">{campaign.pending_drafts}</p>
          <Link href={`/dashboard/campaigns/${id}/drafts`} className="mt-2 inline-block text-xs font-medium text-primary hover:underline">
            Open approval queue →
          </Link>
        </Card>
        <Card className="stat-card">
          <p className="text-sm text-muted">Agent runs</p>
          <p className="mt-2 font-display text-3xl font-bold">{runs?.data?.length ?? 0}</p>
        </Card>
      </div>

      {nextAction.href ? (
        <Card className="flex items-center gap-3 border-primary/20 bg-primary/5 px-4 py-3">
          <CheckCircle2 className="h-5 w-5 text-primary" />
          <Link href={nextAction.href} className="text-sm font-medium text-primary hover:underline">
            {nextAction.text}
          </Link>
        </Card>
      ) : (
        <Card className="flex items-center gap-3 border-teal-200 bg-teal-50/60 px-4 py-3 text-sm text-teal-900">
          <Clock className="h-5 w-5" />
          {nextAction.text}
        </Card>
      )}

      <section>
        <h2 className="font-display text-lg font-semibold">Run history</h2>
        <p className="mt-1 text-sm text-muted">Each run walks through research → drafts → your approval → send.</p>

        <div className="mt-4 space-y-2">
          {(runs?.data ?? []).slice(0, 8).map((run) => {
            const stepMeta = getStepMeta(run.current_step);
            return (
              <Link key={run.id} href={`/dashboard/campaigns/${id}/runs/${run.id}`}>
                <Card className="flex flex-col gap-3 py-4 transition hover:border-primary/30 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <RunStatusBadge status={run.status} pulse={["queued", "running"].includes(run.status)} />
                      {stepMeta && (
                        <span className="text-sm text-muted">· {stepMeta.label}</span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted">{new Date(run.created_at).toLocaleString()}</p>
                  </div>
                  <span className="text-sm font-medium text-primary">View run →</span>
                </Card>
              </Link>
            );
          })}

          {!runs?.data?.length && (
            <Card className="border-dashed text-center text-sm text-muted">
              No runs yet. Add leads, then click <strong>Run agent</strong> above.
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}
