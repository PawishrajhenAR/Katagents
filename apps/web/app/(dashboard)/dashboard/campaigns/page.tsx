"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import type { Campaign, Paginated } from "@/types/api";

export default function CampaignsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => apiFetch<Paginated<Campaign>>("/campaigns"),
  });

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Campaigns</h1>
          <p className="mt-1 text-muted">Manage your outreach campaigns</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/campaigns/new">New campaign</Link>
        </Button>
      </div>

      <div className="mt-8 space-y-3">
        {isLoading && <p className="text-muted">Loading...</p>}
        {(data?.data ?? []).map((c) => (
          <Link key={c.id} href={`/dashboard/campaigns/${c.id}`}>
            <Card className="transition hover:border-primary/40">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{c.name}</p>
                  <p className="text-sm text-muted">{c.agent_type.replace("_", " ")} · {c.status}</p>
                </div>
                <div className="text-right text-sm">
                  <p>{c.lead_count} leads</p>
                  <p className="text-muted">{c.pending_drafts} pending approval</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
