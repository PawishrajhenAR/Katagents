"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import type { AgentMetadata } from "@/types/api";

const comingSoon = [
  { name: "LinkedIn Agent", description: "Automated LinkedIn outreach" },
  { name: "CRM Agent", description: "Sync and update CRM records" },
  { name: "WhatsApp Agent", description: "WhatsApp business messaging" },
  { name: "Voice Calling Agent", description: "AI-powered voice outreach" },
];

export default function AgentsPage() {
  const { data: agents } = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiFetch<AgentMetadata[]>("/agents"),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold">Agents</h1>
      <p className="mt-1 text-muted">Available and upcoming automation agents</p>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {(agents ?? []).map((agent) => (
          <Card key={agent.agent_type}>
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium">{agent.display_name}</p>
                <p className="mt-1 text-sm text-muted">{agent.description}</p>
                <p className="mt-2 text-xs text-muted">v{agent.version}</p>
              </div>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-800">Active</span>
            </div>
            <Button asChild className="mt-4" size="sm">
              <Link href="/dashboard/campaigns/new">Create campaign</Link>
            </Button>
          </Card>
        ))}

        {comingSoon.map((agent) => (
          <Card key={agent.name} className="opacity-60">
            <p className="font-medium">{agent.name}</p>
            <p className="mt-1 text-sm text-muted">{agent.description}</p>
            <span className="mt-4 inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs">Coming soon</span>
          </Card>
        ))}
      </div>
    </div>
  );
}
