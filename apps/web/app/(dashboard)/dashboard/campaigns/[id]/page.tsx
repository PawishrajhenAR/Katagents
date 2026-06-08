"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import type { AgentRun, Campaign, Paginated } from "@/types/api";

const tabs = [
  { href: "", label: "Overview" },
  { href: "/leads", label: "Leads" },
  { href: "/drafts", label: "Drafts" },
  { href: "/inbox", label: "Inbox" },
];

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: campaign } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => apiFetch<Campaign>(`/campaigns/${id}`),
  });

  const { data: runs } = useQuery({
    queryKey: ["runs", id],
    queryFn: () => apiFetch<Paginated<AgentRun>>(`/campaigns/${id}/runs`),
  });

  const startRun = useMutation({
    mutationFn: () =>
      apiFetch<AgentRun>(`/campaigns/${id}/runs`, { method: "POST", body: JSON.stringify({}) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", id] });
    },
  });

  if (!campaign) return <p className="text-muted">Loading...</p>;

  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{campaign.name}</h1>
          <p className="mt-1 text-muted capitalize">{campaign.status} · {campaign.agent_type.replace("_", " ")}</p>
        </div>
        <Button onClick={() => startRun.mutate()} disabled={startRun.isPending}>
          {startRun.isPending ? "Starting..." : "Run agent"}
        </Button>
      </div>

      <nav className="mt-6 flex gap-4 border-b border-border">
        {tabs.map((t) => (
          <Link
            key={t.href}
            href={`/dashboard/campaigns/${id}${t.href}`}
            className="border-b-2 border-transparent pb-2 text-sm text-muted hover:text-foreground data-[active=true]:border-primary"
          >
            {t.label}
          </Link>
        ))}
      </nav>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Card><p className="text-sm text-muted">Leads</p><p className="text-2xl font-semibold">{campaign.lead_count}</p></Card>
        <Card><p className="text-sm text-muted">Pending drafts</p><p className="text-2xl font-semibold">{campaign.pending_drafts}</p></Card>
        <Card><p className="text-sm text-muted">Agent runs</p><p className="text-2xl font-semibold">{runs?.data?.length ?? 0}</p></Card>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-medium">Recent runs</h2>
        <div className="mt-4 space-y-2">
          {(runs?.data ?? []).slice(0, 5).map((run) => (
            <Link key={run.id} href={`/dashboard/campaigns/${id}/runs/${run.id}`}>
              <Card className="flex items-center justify-between py-4 transition hover:border-primary/40">
                <div>
                  <p className="font-medium capitalize">{run.status.replace("_", " ")}</p>
                  <p className="text-sm text-muted">Step: {run.current_step || "—"}</p>
                </div>
                <p className="text-sm text-muted">{new Date(run.created_at).toLocaleString()}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
