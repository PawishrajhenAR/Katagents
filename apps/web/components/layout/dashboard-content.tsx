import { cn } from "@/lib/utils";

/** Shared max-width + centering for all dashboard pages */
export function DashboardContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto w-full min-w-0 max-w-7xl", className)}>{children}</div>
  );
}
