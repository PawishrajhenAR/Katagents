"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, Textarea } from "@/components/ui/input";
import type { Draft, Paginated } from "@/types/api";

export default function CampaignDraftsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["drafts", id],
    queryFn: () => apiFetch<Paginated<Draft>>(`/campaigns/${id}/drafts?status_filter=pending`),
  });

  const approve = useMutation({
    mutationFn: (draftId: string) => apiFetch(`/drafts/${draftId}/approve`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drafts", id] }),
  });

  const reject = useMutation({
    mutationFn: (draftId: string) =>
      apiFetch(`/drafts/${draftId}/reject`, { method: "POST", body: JSON.stringify({ reason: "Needs revision" }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drafts", id] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold">Approval queue</h1>
      <p className="mt-1 text-muted">Review and approve generated emails before sending</p>

      <div className="mt-8 space-y-4">
        {isLoading && <p className="text-muted">Loading...</p>}
        {(data?.data ?? []).map((draft) => (
          <Card key={draft.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-medium">{draft.lead_name || draft.lead_email}</p>
                <p className="text-sm text-muted">{draft.lead_email}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => approve.mutate(draft.id)} disabled={approve.isPending}>
                  Approve
                </Button>
                <Button size="sm" variant="secondary" onClick={() => reject.mutate(draft.id)}>
                  Reject
                </Button>
              </div>
            </div>
            <p className="mt-4 font-medium">{draft.subject}</p>
            <Textarea className="mt-2" readOnly value={draft.body} />
          </Card>
        ))}
        {!isLoading && !data?.data?.length && (
          <Card><p className="text-muted">No pending drafts. Run the agent to generate emails.</p></Card>
        )}
      </div>
    </div>
  );
}
