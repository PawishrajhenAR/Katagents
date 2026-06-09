"use client";

import { Badge } from "@/components/ui/badge";
import { RUN_STATUS_STYLES, formatRunStatus } from "@/lib/agent-steps";
import { cn } from "@/lib/utils";

interface RunStatusBadgeProps {
  status: string;
  pulse?: boolean;
  className?: string;
}

export function RunStatusBadge({ status, pulse, className }: RunStatusBadgeProps) {
  const isActive = ["queued", "running", "waiting_approval"].includes(status);

  return (
    <Badge
      className={cn(
        RUN_STATUS_STYLES[status] ?? "bg-slate-100 text-slate-700",
        pulse && isActive && "agent-status-pulse",
        className,
      )}
    >
      {isActive && (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-40" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
        </span>
      )}
      {formatRunStatus(status)}
    </Badge>
  );
}
