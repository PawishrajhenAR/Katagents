"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Inbox } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { Paginated, Reply } from "@/types/api";

const classificationStyles: Record<string, string> = {
  interested: "bg-emerald-100 text-emerald-800",
  objection: "bg-amber-100 text-amber-800",
  not_now: "bg-blue-100 text-blue-800",
  unsubscribe: "bg-red-100 text-red-800",
  ooo: "bg-slate-100 text-slate-700",
  other: "bg-slate-100 text-slate-600",
};

export default function CampaignInboxPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ["replies", id],
    queryFn: () => apiFetch<Paginated<Reply>>(`/campaigns/${id}/replies`),
  });

  const replies = data?.data ?? [];

  return (
    <div className="space-y-6">
      <Card className="border-border bg-card">
        <p className="text-sm font-medium">Replies land here</p>
        <p className="mt-1 text-sm text-muted">
          When someone responds to a sent email, the AI classifies it (interested, not now, etc.) so you can prioritize.
        </p>
      </Card>

      {isLoading && <p className="text-muted">Loading inbox...</p>}

      {!isLoading && replies.length === 0 && (
        <EmptyState
          icon={Inbox}
          title="Inbox is empty"
          description="Replies appear after emails are sent. With local mock mode, inbox stays empty until you connect Resend."
        />
      )}

      <div className="space-y-4">
        {replies.map((reply) => (
          <Card key={reply.id} className="animate-fade-up">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium">{reply.from_address}</p>
              {reply.classification && (
                <Badge className={classificationStyles[reply.classification] ?? classificationStyles.other}>
                  {reply.classification.replace("_", " ")}
                </Badge>
              )}
            </div>
            <p className="mt-1 text-xs text-muted">{new Date(reply.received_at).toLocaleString()}</p>
            <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed">{reply.body_text}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
