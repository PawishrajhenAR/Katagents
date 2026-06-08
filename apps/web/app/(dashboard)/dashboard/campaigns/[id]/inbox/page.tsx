"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Card } from "@/components/ui/input";
import type { Paginated, Reply } from "@/types/api";

const classificationColors: Record<string, string> = {
  interested: "bg-green-100 text-green-800",
  objection: "bg-yellow-100 text-yellow-800",
  not_now: "bg-blue-100 text-blue-800",
  unsubscribe: "bg-red-100 text-red-800",
  ooo: "bg-gray-100 text-gray-800",
  other: "bg-gray-100 text-gray-600",
};

export default function CampaignInboxPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ["replies", id],
    queryFn: () => apiFetch<Paginated<Reply>>(`/campaigns/${id}/replies`),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold">Inbox</h1>
      <p className="mt-1 text-muted">Inbound replies and AI classifications</p>

      <div className="mt-8 space-y-4">
        {isLoading && <p className="text-muted">Loading...</p>}
        {(data?.data ?? []).map((reply) => (
          <Card key={reply.id}>
            <div className="flex items-center justify-between">
              <p className="font-medium">{reply.from_address}</p>
              {reply.classification && (
                <span className={`rounded-full px-2 py-0.5 text-xs capitalize ${classificationColors[reply.classification] || classificationColors.other}`}>
                  {reply.classification.replace("_", " ")}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-muted">{new Date(reply.received_at).toLocaleString()}</p>
            <p className="mt-3 whitespace-pre-wrap text-sm">{reply.body_text}</p>
          </Card>
        ))}
        {!isLoading && !data?.data?.length && (
          <Card><p className="text-muted">No replies yet.</p></Card>
        )}
      </div>
    </div>
  );
}
