"use client";

import { useParams } from "next/navigation";
import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiUpload } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import type { Lead, LeadImportResult, Paginated } from "@/types/api";

export default function CampaignLeadsPage() {
  const { id } = useParams<{ id: string }>();
  const fileRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["leads", id],
    queryFn: () => apiFetch<Paginated<Lead>>(`/campaigns/${id}/leads`),
  });

  const importCsv = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return apiUpload<LeadImportResult>(`/campaigns/${id}/leads/import`, fd);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    },
  });

  const addLead = useMutation({
    mutationFn: (body: { email: string; first_name?: string; company?: string }) =>
      apiFetch(`/campaigns/${id}/leads`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leads", id] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold">Leads</h1>
      <div className="mt-6 flex flex-wrap gap-3">
        <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) importCsv.mutate(f);
        }} />
        <Button variant="secondary" onClick={() => fileRef.current?.click()} disabled={importCsv.isPending}>
          {importCsv.isPending ? "Importing..." : "Import CSV"}
        </Button>
        <Button onClick={() => addLead.mutate({ email: "prospect@example.com", first_name: "Jane", company: "Acme" })}>
          Add sample lead
        </Button>
      </div>
      {importCsv.data && (
        <p className="mt-2 text-sm text-muted">
          Imported {importCsv.data.imported}, skipped {importCsv.data.skipped}
        </p>
      )}

      <div className="mt-8 overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-card">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Email</th>
              <th className="px-4 py-3 text-left font-medium">Name</th>
              <th className="px-4 py-3 text-left font-medium">Company</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={4} className="px-4 py-6 text-muted">Loading...</td></tr>
            )}
            {(data?.data ?? []).map((lead) => (
              <tr key={lead.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3">{lead.email}</td>
                <td className="px-4 py-3">{[lead.first_name, lead.last_name].filter(Boolean).join(" ") || "—"}</td>
                <td className="px-4 py-3">{lead.company || "—"}</td>
                <td className="px-4 py-3 capitalize">{lead.campaign_status || lead.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
