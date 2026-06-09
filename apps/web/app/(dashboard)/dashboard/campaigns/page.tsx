"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Mail, Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { Campaign, Paginated } from "@/types/api";

export default function CampaignsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => apiFetch<Paginated<Campaign>>("/campaigns"),
  });

  const campaigns = data?.data ?? [];

  return (
    <div className="w-full min-w-0 space-y-8 animate-fade-up">
      <PageHeader
        title="Campaigns"
        description="Each campaign is one outreach project. The agent runs on its leads independently."
        actions={
          <Button asChild>
            <Link href="/dashboard/campaigns/new">
              <Plus className="h-4 w-4" /> New campaign
            </Link>
          </Button>
        }
      />

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl skeleton-shimmer" />
          ))}
        </div>
      )}

      {!isLoading && campaigns.length === 0 && (
        <EmptyState
          icon={Mail}
          title="No campaigns yet"
          description="Create a campaign to organize your leads and run the email outreach agent."
          action={{ label: "Create campaign", href: "/dashboard/campaigns/new" }}
        />
      )}

      <div className="space-y-3">
        {campaigns.map((c) => (
          <Link key={c.id} href={`/dashboard/campaigns/${c.id}`}>
            <Card className="stat-card">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-display text-lg font-semibold">{c.name}</p>
                  <p className="mt-1 text-sm text-muted">
                    Email outreach · {c.lead_count} leads · {c.pending_drafts} pending approval
                  </p>
                </div>
                <span className="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-medium capitalize text-primary">
                  {c.status}
                </span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
