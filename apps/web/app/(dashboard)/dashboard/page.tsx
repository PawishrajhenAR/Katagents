"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { Card } from "@/components/ui/input";
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

  const stats = [
    { label: "Active campaigns", value: overview?.active_campaigns ?? 0 },
    { label: "Total leads", value: overview?.total_leads ?? 0 },
    { label: "Emails sent", value: overview?.emails_sent ?? 0 },
    { label: "Pending approvals", value: overview?.pending_approvals ?? 0 },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-muted">Overview of your agent automation platform</p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <p className="text-sm text-muted">{s.label}</p>
            <p className="mt-2 text-3xl font-semibold">{s.value}</p>
          </Card>
        ))}
      </div>

      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Recent campaigns</h2>
          <Link href="/dashboard/campaigns/new" className="text-sm text-primary hover:underline">
            New campaign
          </Link>
        </div>
        <div className="mt-4 space-y-3">
          {(campaigns?.data ?? []).map((c) => (
            <Link key={c.id} href={`/dashboard/campaigns/${c.id}`}>
              <Card className="transition hover:border-primary/40">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{c.name}</p>
                    <p className="text-sm text-muted">{c.agent_type} · {c.status}</p>
                  </div>
                  <div className="text-right text-sm text-muted">
                    <p>{c.lead_count} leads</p>
                    <p>{c.pending_drafts} pending drafts</p>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
          {!campaigns?.data?.length && (
            <Card>
              <p className="text-muted">No campaigns yet. Create your first email outreach campaign.</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
