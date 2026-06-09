"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { AnalyticsOverview } from "@/types/api";

export default function AnalyticsPage() {
  const { data } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => apiFetch<AnalyticsOverview>("/analytics/overview"),
  });

  const metrics = [
    { label: "Total campaigns", value: data?.total_campaigns ?? 0, hint: "All time" },
    { label: "Active now", value: data?.active_campaigns ?? 0, hint: "Running outreach" },
    { label: "Leads tracked", value: data?.total_leads ?? 0, hint: "Across campaigns" },
    { label: "Emails sent", value: data?.emails_sent ?? 0, hint: "Including mock sends" },
    { label: "Replies", value: data?.replies_received ?? 0, hint: "Inbound responses" },
    { label: "Reply rate", value: `${data?.reply_rate ?? 0}%`, hint: "Of sent emails" },
    { label: "Awaiting approval", value: data?.pending_approvals ?? 0, hint: "Drafts you need to review" },
  ];

  return (
    <div className="w-full min-w-0 space-y-8 animate-fade-up">
      <PageHeader
        title="Analytics"
        description="High-level numbers across your workspace. Per-campaign detail lives inside each campaign."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((m) => (
          <Card key={m.label} className="stat-card">
            <div className="flex items-start justify-between">
              <p className="text-sm text-muted">{m.label}</p>
              <BarChart3 className="h-4 w-4 text-primary/50" />
            </div>
            <p className="mt-3 font-display text-3xl font-bold">{m.value}</p>
            <p className="mt-1 text-xs text-muted">{m.hint}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
