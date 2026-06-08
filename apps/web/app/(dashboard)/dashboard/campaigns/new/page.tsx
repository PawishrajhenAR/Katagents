"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, Input, Label } from "@/components/ui/input";
import type { Campaign } from "@/types/api";

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
    onSuccess: (campaign) => router.push(`/dashboard/campaigns/${campaign.id}`),
  });

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-semibold">New campaign</h1>
      <Card className="mt-6 space-y-4">
        <div>
          <Label htmlFor="name">Campaign name</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Q2 SaaS outreach" />
        </div>
        <div>
          <Label htmlFor="tone">Email tone</Label>
          <Input id="tone" value={tone} onChange={(e) => setTone(e.target.value)} />
        </div>
        <Button onClick={() => mutation.mutate()} disabled={!name || mutation.isPending}>
          {mutation.isPending ? "Creating..." : "Create campaign"}
        </Button>
      </Card>
    </div>
  );
}
