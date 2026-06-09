"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Bot, Mail, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { AgentPipeline } from "@/components/agents/agent-pipeline";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { AgentMetadata } from "@/types/api";

const comingSoon = [
  { name: "LinkedIn Agent", description: "Automated connection requests and follow-ups" },
  { name: "CRM Agent", description: "Keep your CRM updated from conversations" },
  { name: "WhatsApp Agent", description: "Business messaging at scale" },
];

export default function AgentsPage() {
  const { data: agents } = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiFetch<AgentMetadata[]>("/agents"),
  });

  return (
    <div className="w-full min-w-0 space-y-10 animate-fade-up">
      <PageHeader
        title="Agents"
        description="Specialized AI workers that run multi-step automations. Start with Email Outreach — more agents coming soon."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {(agents ?? []).map((agent) => (
          <Card key={agent.agent_type} className="relative overflow-hidden border-teal-200 p-0">
            <div className="bg-gradient-to-br from-teal-500/10 via-transparent to-transparent px-6 py-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-500 text-white shadow-lg shadow-teal-500/30">
                    <Mail className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-display text-xl font-bold">{agent.display_name}</p>
                    <p className="text-xs text-muted">v{agent.version} · Ready for local use</p>
                  </div>
                </div>
                <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                  Active
                </span>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-muted">{agent.description}</p>
            </div>

            <div className="border-t border-border px-4 py-5">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">What it does</p>
              <AgentPipeline compact />
            </div>

            <div className="border-t border-border px-6 py-4">
              <Button asChild className="w-full sm:w-auto">
                <Link href="/dashboard/campaigns/new">
                  <Sparkles className="h-4 w-4" /> Start a campaign
                </Link>
              </Button>
            </div>
          </Card>
        ))}

        {comingSoon.map((agent) => (
          <Card key={agent.name} className="opacity-55">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
                <Bot className="h-6 w-6" />
              </div>
              <div>
                <p className="font-display font-semibold">{agent.name}</p>
                <p className="mt-1 text-sm text-muted">{agent.description}</p>
                <span className="mt-3 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs">Coming soon</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
