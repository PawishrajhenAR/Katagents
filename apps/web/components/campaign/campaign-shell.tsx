"use client";

import Link from "next/link";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Play, Zap } from "lucide-react";
import { AgentPipeline } from "@/components/agents/agent-pipeline";
import { RunStatusBadge } from "@/components/agents/run-status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { AgentRun, Campaign, Paginated } from "@/types/api";

const tabs = [
  { href: "", label: "Overview", hint: "Status & runs" },
  { href: "/leads", label: "Leads", hint: "Your contacts" },
  { href: "/drafts", label: "Drafts", hint: "Approve emails" },
  { href: "/inbox", label: "Inbox", hint: "Replies" },
];

export function CampaignShell({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const isRunPage = pathname.includes("/runs/");

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

  const startRun = useMutation({
    mutationFn: () =>
      apiFetch<AgentRun>(`/campaigns/${id}/runs`, { method: "POST", body: JSON.stringify({}) }),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["runs", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
      router.push(`/dashboard/campaigns/${id}/runs/${run.id}`);
    },
  });

  const activeRun = runs?.data?.find((r) =>
    ["queued", "running", "waiting_approval"].includes(r.status),
  );

  if (!campaign) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="flex items-center gap-3 text-muted">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          Loading campaign...
        </div>
      </div>
    );
  }

  if (isRunPage) {
    return <div className="animate-fade-up">{children}</div>;
  }

  const base = `/dashboard/campaigns/${id}`;

  return (
    <div className="w-full min-w-0 space-y-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <Link href="/dashboard/campaigns" className="inline-flex items-center gap-1 text-sm text-muted hover:text-primary">
            <ArrowLeft className="h-4 w-4" /> All campaigns
          </Link>
          <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight">{campaign.name}</h1>
          <p className="mt-2 max-w-xl text-muted">
            Email outreach agent · {campaign.lead_count} leads · {campaign.pending_drafts} drafts waiting
          </p>
        </div>

        <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
          {activeRun && (
            <Link href={`${base}/runs/${activeRun.id}`}>
              <Card className="flex items-center gap-3 border-teal-200 bg-teal-50/80 px-4 py-3">
                <Zap className="h-4 w-4 text-teal-600" />
                <div>
                  <p className="text-xs font-medium text-teal-800">Agent active</p>
                  <RunStatusBadge status={activeRun.status} pulse className="mt-1" />
                </div>
              </Card>
            </Link>
          )}
          <Button
            size="lg"
            onClick={() => startRun.mutate()}
            disabled={startRun.isPending || campaign.lead_count === 0}
            className="shadow-lg shadow-primary/20"
          >
            <Play className="h-4 w-4" />
            {startRun.isPending ? "Starting..." : "Run agent"}
          </Button>
        </div>
      </div>

      {campaign.lead_count === 0 && (
        <Card className="border-amber-200 bg-amber-50/60 px-4 py-3 text-sm text-amber-900">
          Add leads first — go to the <Link href={`${base}/leads`} className="font-semibold underline">Leads tab</Link> and import a CSV or add a test contact.
        </Card>
      )}

      <Card className="overflow-hidden p-0">
        <div className="border-b border-border bg-gradient-to-r from-teal-500/5 via-transparent to-transparent px-6 py-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">Agent pipeline</p>
          <p className="mt-1 text-sm text-muted">What happens when you click Run agent</p>
        </div>
        <div className="overflow-x-auto px-4 py-6 sm:px-6">
          <div className="min-w-[320px]">
            <AgentPipeline
              currentStep={activeRun?.current_step}
              compact
            />
          </div>
        </div>
      </Card>

      <nav className="flex flex-wrap gap-1 rounded-xl border border-border bg-card p-1">
        {tabs.map((t) => {
          const href = `${base}${t.href}`;
          const active = t.href === "" ? pathname === base : pathname.startsWith(href);

          return (
            <Link
              key={t.href}
              href={href}
              className={cn(
                "flex min-w-[7rem] flex-1 flex-col rounded-lg px-4 py-3 transition-all",
                (active)
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted hover:bg-background hover:text-foreground",
              )}
            >
              <span className="text-sm font-semibold">{t.label}</span>
              <span className={cn("text-xs", active ? "text-primary-foreground/80" : "")}>
                {t.hint}
              </span>
            </Link>
          );
        })}
      </nav>

      <div>{children}</div>
    </div>
  );
}
