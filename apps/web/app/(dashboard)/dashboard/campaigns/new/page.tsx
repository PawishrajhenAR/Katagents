"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { ProcessGuide } from "@/components/workflow/process-guide";
import { AgentPipeline } from "@/components/agents/agent-pipeline";
import { Button } from "@/components/ui/button";
import { Card, Input, Label } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { Campaign } from "@/types/api";

const TONE_OPTIONS = [
  { value: "professional", label: "Professional", hint: "Clear and respectful — best default" },
  { value: "friendly", label: "Friendly", hint: "Warm and conversational" },
  { value: "direct", label: "Direct", hint: "Short and to the point" },
];

export default function NewCampaignPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [tone, setTone] = useState("professional");

  const mutation = useMutation({
    mutationFn: () =>
      apiFetch<Campaign>("/campaigns", {
        method: "POST",
        body: JSON.stringify({
          name,
          agent_type: "email_outreach",
          config_json: { tone, require_approval: true, follow_up_delay_days: 7 },
        }),
      }),
    onSuccess: (campaign) => router.push(`/dashboard/campaigns/${campaign.id}/leads`),
  });

  return (
    <div className="flex w-full min-w-0 flex-col gap-8 animate-fade-up">
      <div className="shrink-0 space-y-6">
        <Link
          href="/dashboard/campaigns"
          className="inline-flex items-center gap-1 text-sm text-muted hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" /> Back to campaigns
        </Link>

        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">New campaign</h1>
          <p className="mt-2 text-muted">Step 1 of 4 — name your project. You&apos;ll add leads next.</p>
        </div>

        <ProcessGuide activeStep={1} compact />
      </div>

      <div className="min-w-0 space-y-8 pb-4">
        <Card className="space-y-6">
          <div>
            <Label htmlFor="name">Campaign name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Q2 SaaS founders outreach"
              className="mt-2"
            />
            <p className="mt-2 text-xs text-muted">Something you&apos;ll recognize later — not shown to leads.</p>
          </div>

          <div>
            <Label>Email tone</Label>
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              {TONE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setTone(opt.value)}
                  className={`rounded-xl border p-3 text-left transition-all ${
                    tone === opt.value
                      ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                      : "border-border hover:border-primary/30"
                  }`}
                >
                  <p className="text-sm font-semibold">{opt.label}</p>
                  <p className="mt-1 text-xs text-muted">{opt.hint}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-xl bg-teal-50/80 px-4 py-3 text-sm text-teal-900">
            <Sparkles className="mb-1 inline h-4 w-4" /> Approval is always on — nothing sends until you approve each draft.
          </div>

          <Button
            size="lg"
            className="w-full sm:w-auto"
            onClick={() => mutation.mutate()}
            disabled={!name.trim() || mutation.isPending}
          >
            {mutation.isPending ? "Creating..." : "Create & add leads →"}
          </Button>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-6 py-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">Preview: agent pipeline</p>
          </div>
          <div className="overflow-x-auto px-4 py-6 sm:px-6">
            <div className="min-w-[320px]">
              <AgentPipeline compact />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
