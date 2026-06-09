"use client";

import { CampaignShell } from "@/components/campaign/campaign-shell";

export default function CampaignLayout({ children }: { children: React.ReactNode }) {
  return <CampaignShell>{children}</CampaignShell>;
}
