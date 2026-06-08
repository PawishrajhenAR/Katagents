"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Card } from "@/components/ui/input";
interface MemberOut {
  id: string;
  user_id: string;
  org_id: string;
  role: string;
  user?: { id: string; email: string; name: string; is_active: boolean };
}

export default function TeamSettingsPage() {
  const { data: members } = useQuery({
    queryKey: ["members"],
    queryFn: () => apiFetch<MemberOut[]>("/organizations/members"),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold">Team</h1>
      <div className="mt-8 space-y-3">
        {(members ?? []).map((m) => (
          <Card key={m.id} className="flex items-center justify-between py-4">
            <div>
              <p className="font-medium">{m.user?.name}</p>
              <p className="text-sm text-muted">{m.user?.email}</p>
            </div>
            <span className="capitalize text-sm">{m.role}</span>
          </Card>
        ))}
      </div>
    </div>
  );
}
