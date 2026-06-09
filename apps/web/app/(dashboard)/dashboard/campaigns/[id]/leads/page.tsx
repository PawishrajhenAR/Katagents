"use client";

import { useParams } from "next/navigation";
import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, FileUp, RotateCcw, Trash2, UserPlus } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, Input, Label } from "@/components/ui/input";
import { apiFetch, apiUpload } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { Lead, LeadImportResult, Paginated } from "@/types/api";

function statusBadgeClass(status: string | null | undefined) {
  switch (status) {
    case "skipped":
      return "bg-amber-100 text-amber-800";
    case "sent":
    case "replied":
      return "bg-emerald-100 text-emerald-800";
    case "ready":
      return "bg-teal-100 text-teal-800";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

const emptyForm = {
  email: "",
  first_name: "",
  last_name: "",
  company: "",
  title: "",
};

export default function CampaignLeadsPage() {
  const { id } = useParams<{ id: string }>();
  const fileRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState("");

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
    mutationFn: (body: {
      email: string;
      first_name?: string;
      last_name?: string;
      company?: string;
      title?: string;
    }) => apiFetch(`/campaigns/${id}/leads`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
      setForm(emptyForm);
      setFormError("");
    },
    onError: (err) => {
      setFormError(err instanceof Error ? err.message : "Could not add lead");
    },
  });

  const excludeLead = useMutation({
    mutationFn: (leadId: string) =>
      apiFetch(`/campaigns/${id}/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: "skipped" }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    },
  });

  const includeLead = useMutation({
    mutationFn: (leadId: string) =>
      apiFetch(`/campaigns/${id}/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: "ready" }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    },
  });

  const removeLead = useMutation({
    mutationFn: (leadId: string) =>
      apiFetch(`/campaigns/${id}/leads/${leadId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads", id] });
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    },
  });

  const handleRemove = (lead: Lead) => {
    const ok = window.confirm(
      `Remove ${lead.email} from this campaign? They won't be contacted in this outreach.`,
    );
    if (ok) removeLead.mutate(lead.id);
  };

  const leads = data?.data ?? [];

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    const email = form.email.trim();
    if (!email || !email.includes("@")) {
      setFormError("Enter a valid email address.");
      return;
    }
    addLead.mutate({
      email,
      first_name: form.first_name.trim() || undefined,
      last_name: form.last_name.trim() || undefined,
      company: form.company.trim() || undefined,
      title: form.title.trim() || undefined,
    });
  };

  const fillSample = () => {
    setForm({
      email: "prospect@example.com",
      first_name: "Jane",
      last_name: "Doe",
      company: "Acme Inc",
      title: "Head of Growth",
    });
    setFormError("");
  };

  return (
    <div className="space-y-6">
      <Card className="border-primary/20 bg-primary/5">
        <p className="text-sm font-medium text-foreground">Step 2 — Add who you want to reach</p>
        <p className="mt-1 text-sm text-muted">
          Add leads one at a time below, or import many at once with a CSV file.
        </p>
      </Card>

      <div className="grid min-w-0 gap-6 lg:grid-cols-2">
        <Card>
          <div className="flex items-center gap-2">
            <UserPlus className="h-4 w-4 text-primary" />
            <h2 className="font-display font-semibold">Add manually</h2>
          </div>
          <p className="mt-1 text-sm text-muted">Email is required. Other fields help the agent personalize.</p>

          <form onSubmit={handleManualSubmit} className="mt-5 space-y-4">
            <div>
              <Label htmlFor="lead-email">Email *</Label>
              <Input
                id="lead-email"
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="jane@company.com"
                className="mt-1.5"
                required
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="lead-first">First name</Label>
                <Input
                  id="lead-first"
                  value={form.first_name}
                  onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                  placeholder="Jane"
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="lead-last">Last name</Label>
                <Input
                  id="lead-last"
                  value={form.last_name}
                  onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                  placeholder="Doe"
                  className="mt-1.5"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="lead-company">Company</Label>
              <Input
                id="lead-company"
                value={form.company}
                onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}
                placeholder="Acme Inc"
                className="mt-1.5"
              />
            </div>

            <div>
              <Label htmlFor="lead-title">Job title</Label>
              <Input
                id="lead-title"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Head of Marketing"
                className="mt-1.5"
              />
            </div>

            {formError && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</p>
            )}

            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={addLead.isPending}>
                {addLead.isPending ? "Adding..." : "Add lead"}
              </Button>
              <Button type="button" variant="secondary" size="sm" onClick={fillSample}>
                Fill sample data
              </Button>
            </div>
          </form>
        </Card>

        <Card>
          <div className="flex items-center gap-2">
            <FileUp className="h-4 w-4 text-primary" />
            <h2 className="font-display font-semibold">Import CSV</h2>
          </div>
          <p className="mt-1 text-sm text-muted">Bulk import from a spreadsheet export.</p>

          <div className="mt-5 rounded-xl border border-dashed border-border bg-background/50 p-6 text-center">
            <p className="text-sm text-muted">
              Required column: <code className="rounded bg-card px-1">email</code>
            </p>
            <p className="mt-2 text-xs text-muted">
              Optional: first_name, last_name, company, title
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importCsv.mutate(f);
                e.target.value = "";
              }}
            />
            <Button
              variant="secondary"
              className="mt-4"
              onClick={() => fileRef.current?.click()}
              disabled={importCsv.isPending}
            >
              <FileUp className="h-4 w-4" />
              {importCsv.isPending ? "Importing..." : "Choose CSV file"}
            </Button>
          </div>

          {importCsv.data && (
            <p className="mt-4 text-sm text-emerald-700">
              Imported {importCsv.data.imported} leads · skipped {importCsv.data.skipped}
            </p>
          )}
        </Card>
      </div>

      {!isLoading && leads.length === 0 ? (
        <EmptyState
          icon={UserPlus}
          title="No leads yet"
          description="Add a lead manually or import a CSV, then go to Overview and click Run agent."
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-medium">{leads.length} lead{leads.length !== 1 ? "s" : ""} in this campaign</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="border-b border-border bg-background/80">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Email</th>
                  <th className="px-4 py-3 text-left font-medium">Name</th>
                  <th className="px-4 py-3 text-left font-medium">Company</th>
                  <th className="px-4 py-3 text-left font-medium">Title</th>
                  <th className="px-4 py-3 text-left font-medium">Status</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted">
                      Loading leads...
                    </td>
                  </tr>
                )}
                {leads.map((lead) => {
                  const status = lead.campaign_status || lead.status;
                  const isSkipped = status === "skipped";
                  const isBusy =
                    excludeLead.isPending || includeLead.isPending || removeLead.isPending;

                  return (
                    <tr
                      key={lead.id}
                      className={cn(
                        "border-b border-border last:border-0 hover:bg-background/50",
                        isSkipped && "bg-amber-50/40 opacity-80",
                      )}
                    >
                      <td className="px-4 py-3 font-medium">{lead.email}</td>
                      <td className="px-4 py-3">
                        {[lead.first_name, lead.last_name].filter(Boolean).join(" ") || "—"}
                      </td>
                      <td className="px-4 py-3">{lead.company || "—"}</td>
                      <td className="px-4 py-3">{lead.title || "—"}</td>
                      <td className="px-4 py-3">
                        <Badge className={statusBadgeClass(status)}>{status}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          {isSkipped ? (
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={isBusy}
                              onClick={() => includeLead.mutate(lead.id)}
                              title="Include in agent runs again"
                            >
                              <RotateCcw className="h-3.5 w-3.5" />
                              Include
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={isBusy || status === "sent"}
                              onClick={() => excludeLead.mutate(lead.id)}
                              title="Exclude from agent — stays in list but won't be contacted"
                            >
                              <Ban className="h-3.5 w-3.5" />
                              Exclude
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-600 hover:bg-red-50 hover:text-red-700"
                            disabled={isBusy}
                            onClick={() => handleRemove(lead)}
                            title="Remove from this campaign"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
