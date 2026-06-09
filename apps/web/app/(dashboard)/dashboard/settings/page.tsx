"use client";

import Link from "next/link";
import { Key, Users } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/input";

const sections = [
  {
    href: "/dashboard/settings/team",
    icon: Users,
    title: "Team",
    description: "Invite teammates and set roles — Manager, Reviewer, Viewer.",
  },
  {
    href: "/dashboard/settings/integrations",
    icon: Key,
    title: "Integrations",
    description: "Add Gemini and Resend API keys in apps/api/.env for real AI and email.",
  },
];

export default function SettingsPage() {
  return (
    <div className="w-full min-w-0 space-y-8 animate-fade-up">
      <PageHeader
        title="Settings"
        description="Workspace configuration for local development."
      />

      <div className="grid gap-4">
        {sections.map(({ href, icon: Icon, title, description }) => (
          <Link key={href} href={href}>
            <Card className="stat-card flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="font-display font-semibold">{title}</p>
                <p className="mt-1 text-sm text-muted">{description}</p>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
