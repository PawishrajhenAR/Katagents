import { cn } from "@/lib/utils";

export function Badge({
  className,
  children,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
