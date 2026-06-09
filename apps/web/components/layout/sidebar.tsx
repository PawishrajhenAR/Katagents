import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bot,
  LayoutDashboard,
  LogOut,
  Mail,
  Settings,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/auth-provider";

const nav = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard, hint: "Start here" },
  { href: "/dashboard/campaigns", label: "Campaigns", icon: Mail, hint: "Your outreach" },
  { href: "/dashboard/agents", label: "Agents", icon: Bot, hint: "Automation types" },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3, hint: "Results" },
  { href: "/dashboard/settings", label: "Settings", icon: Settings, hint: "Team & keys" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, org, logout } = useAuth();

  return (
    <aside className="sticky top-0 flex h-screen w-72 shrink-0 flex-col overflow-hidden border-r border-white/5 bg-sidebar text-sidebar-foreground">
      <div className="border-b border-white/10 p-6">
        <Logo
          size="md"
          href="/dashboard"
          wordmarkClassName="text-white"
          imageClassName="rounded-xl"
        />
        <p className="mt-4 truncate rounded-lg bg-white/5 px-3 py-2 text-xs text-white/70">
          {org?.name || "Your workspace"}
        </p>
      </div>

      <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto p-4">
        {nav.map(({ href, label, icon: Icon, hint }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all",
                active
                  ? "bg-teal-500/15 text-white ring-1 ring-teal-400/30"
                  : "text-white/65 hover:bg-white/5 hover:text-white",
              )}
            >
              <Icon className={cn("h-4 w-4 shrink-0", active && "text-teal-300")} />
              <div className="min-w-0">
                <p className="text-sm font-medium">{label}</p>
                <p className="text-[11px] text-white/40 group-hover:text-white/55">{hint}</p>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <p className="truncate text-sm font-medium">{user?.name}</p>
        <p className="truncate text-xs text-white/50">{user?.email}</p>
        <Button
          variant="ghost"
          size="sm"
          className="mt-3 w-full justify-start text-white/70 hover:bg-white/5 hover:text-white"
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </Button>
      </div>
    </aside>
  );
}
