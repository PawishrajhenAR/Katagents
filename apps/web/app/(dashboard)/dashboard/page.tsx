"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Mail, Plus, Sparkles, Users } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ProcessGuide } from "@/components/workflow/process-guide";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { AnalyticsOverview, Paginated, Campaign } from "@/types/api";

export default function DashboardPage() {
  const { data: overview } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => apiFetch<AnalyticsOverview>("/analytics/overview"),
  });

  const { data: campaigns } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => apiFetch<Paginated<Campaign>>("/campaigns?per_page=5"),
  });

  const hasCampaigns = (campaigns?.data?.length ?? 0) > 0;
  const activeStep = !hasCampaigns ? 1 : (overview?.pending_approvals ?? 0) > 0 ? 4 : 3;

  const stats = [
    { label: "Active campaigns", value: overview?.active_campaigns ?? 0, icon: Sparkles },
    { label: "Total leads", value: overview?.total_leads ?? 0, icon: Users },
    { label: "Emails sent", value: overview?.emails_sent ?? 0, icon: Mail },
    { label: "Awaiting your OK", value: overview?.pending_approvals ?? 0, icon: Mail },
  ];

  return (
    <div className="w-full min-w-0 space-y-10">
      <PageHeader
        title="Welcome back"
        description="Your AI agents handle research, writing, and follow-ups — you stay in control of what gets sent."
        hint="Tip: Create a campaign → add leads → Run agent → approve drafts."
        actions={
          <Button asChild size="lg" className="shadow-lg shadow-primary/20">
            <Link href="/dashboard/campaigns/new">
              <Plus className="h-4 w-4" /> New campaign
            </Link>
          </Button>
        }
      />

      <ProcessGuide activeStep={activeStep} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <Card key={label} className="stat-card">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted">{label}</p>
              <Icon className="h-4 w-4 text-primary/70" />
            </div>
            <p className="mt-3 font-display text-3xl font-bold">{value}</p>
          </Card>
        ))}
      </div>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-xl font-semibold">Recent campaigns</h2>
          <Link href="/dashboard/campaigns" className="text-sm font-medium text-primary hover:underline">
            View all
          </Link>
        </div>

        <div className="space-y-3">
          {(campaigns?.data ?? []).map((c) => (
            <Link key={c.id} href={`/dashboard/campaigns/${c.id}`}>
              <Card className="transition hover:border-primary/30 hover:shadow-md">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-display text-lg font-semibold">{c.name}</p>
                    <p className="mt-1 text-sm text-muted">
                      {c.lead_count} leads · {c.pending_drafts} drafts to review
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {c.pending_drafts > 0 && (
                      <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
                        Needs approval
                      </span>
                    )}
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs capitalize text-slate-700">
                      {c.status}
                    </span>
                  </div>
                </div>
              </Card>
            </Link>
          ))}

          {!hasCampaigns && (
            <Card className="border-dashed text-center">
              <p className="text-muted">No campaigns yet.</p>
              <Button asChild className="mt-4">
                <Link href="/dashboard/campaigns/new">Create your first campaign</Link>
              </Button>
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}
