"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Card } from "@/components/ui/input";
import type { AnalyticsOverview } from "@/types/api";

export default function AnalyticsPage() {
  const { data } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => apiFetch<AnalyticsOverview>("/analytics/overview"),
  });

  const metrics = [
    { label: "Total campaigns", value: data?.total_campaigns ?? 0 },
    { label: "Active campaigns", value: data?.active_campaigns ?? 0 },
    { label: "Total leads", value: data?.total_leads ?? 0 },
    { label: "Emails sent", value: data?.emails_sent ?? 0 },
    { label: "Delivered", value: data?.emails_delivered ?? 0 },
    { label: "Replies", value: data?.replies_received ?? 0 },
    { label: "Reply rate", value: `${data?.reply_rate ?? 0}%` },
    { label: "Pending approvals", value: data?.pending_approvals ?? 0 },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <p className="mt-1 text-muted">Platform performance metrics</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label}>
            <p className="text-sm text-muted">{m.label}</p>
            <p className="mt-2 text-2xl font-semibold">{m.value}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
