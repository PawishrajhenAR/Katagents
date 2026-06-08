"use client";

import Link from "next/link";
import { Card } from "@/components/ui/input";

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Settings</h1>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <Link href="/dashboard/settings/team">
          <Card className="transition hover:border-primary/40">
            <p className="font-medium">Team</p>
            <p className="mt-1 text-sm text-muted">Manage members and roles</p>
          </Card>
        </Link>
        <Link href="/dashboard/settings/integrations">
          <Card className="transition hover:border-primary/40">
            <p className="font-medium">Integrations</p>
            <p className="mt-1 text-sm text-muted">Configure Resend and AI providers</p>
          </Card>
        </Link>
      </div>
    </div>
  );
}
