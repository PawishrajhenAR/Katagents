import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  hint?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, hint, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("animate-fade-up flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between", className)}>
      <div className="min-w-0 flex-1">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">{title}</h1>
        {description && <p className="mt-2 text-base text-muted">{description}</p>}
        {hint && (
          <p className="mt-3 inline-flex rounded-lg bg-primary/5 px-3 py-2 text-sm text-primary">{hint}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
