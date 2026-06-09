"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";
import { Card, Textarea } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import type { Draft, Paginated } from "@/types/api";

export default function CampaignDraftsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["drafts", id],
    queryFn: () => apiFetch<Paginated<Draft>>(`/campaigns/${id}/drafts?status_filter=pending`),
    refetchInterval: 5000,
  });

  const approve = useMutation({
    mutationFn: (draftId: string) => apiFetch(`/drafts/${draftId}/approve`, { method: "POST" }),
    onMutate: async (draftId) => {
      await queryClient.cancelQueries({ queryKey: ["drafts", id] });
      const previous = queryClient.getQueryData<Paginated<Draft>>(["drafts", id]);
      queryClient.setQueryData<Paginated<Draft>>(["drafts", id], (old) =>
        old
          ? { ...old, data: old.data.filter((d) => d.id !== draftId) }
          : old,
      );
      return { previous };
    },
    onError: (_err, _draftId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["drafts", id], context.previous);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drafts", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
      queryClient.invalidateQueries({ queryKey: ["runs", id] });
    },
  });

  const reject = useMutation({
    mutationFn: (draftId: string) =>
      apiFetch(`/drafts/${draftId}/reject`, { method: "POST", body: JSON.stringify({ reason: "Needs revision" }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drafts", id] }),
  });

  const drafts = data?.data ?? [];

  return (
    <div className="space-y-6">
      <Card className="border-amber-200 bg-amber-50/60">
        <p className="text-sm font-medium text-amber-950">Step 4 — You&apos;re in control</p>
        <p className="mt-1 text-sm text-amber-900/80">
          Approve emails you like. When all pending drafts are approved, the agent automatically continues and sends them.
        </p>
      </Card>

      <div className="space-y-4">
        {isLoading && (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-40 rounded-xl skeleton-shimmer" />
            ))}
          </div>
        )}

        {drafts.map((draft) => (
          <Card key={draft.id} className="animate-fade-up overflow-hidden p-0">
            <div className="flex flex-col gap-4 border-b border-border bg-background/50 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-display font-semibold">{draft.lead_name || "Prospect"}</p>
                <p className="text-sm text-muted">{draft.lead_email}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => approve.mutate(draft.id)} disabled={approve.isPending}>
                  <Check className="h-4 w-4" /> Approve
                </Button>
                <Button size="sm" variant="secondary" onClick={() => reject.mutate(draft.id)}>
                  <X className="h-4 w-4" /> Reject
                </Button>
              </div>
            </div>
            <div className="px-6 py-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">Subject</p>
              <p className="mt-1 font-medium">{draft.subject}</p>
              <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-muted">Body</p>
              <Textarea className="mt-2 bg-background/50" readOnly value={draft.body} />
            </div>
          </Card>
        ))}

        {!isLoading && drafts.length === 0 && (
          <EmptyState
            icon={Check}
            title="No drafts waiting"
            description="Run the agent from the Overview tab. Generated emails will show up here for your approval."
          />
        )}
      </div>
    </div>
  );
}
