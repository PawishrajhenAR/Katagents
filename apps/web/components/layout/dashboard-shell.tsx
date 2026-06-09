"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { Logo } from "@/components/brand/logo";
import { useAuth } from "@/providers/auth-provider";
import { ROUTES } from "@/lib/constants";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace(ROUTES.login);
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center dashboard-bg">
        <div className="flex flex-col items-center gap-4 animate-fade-up">
          <Logo size="lg" showWordmark href="/dashboard" />
          <div className="flex flex-col items-center gap-2">
            <span className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm text-muted">Loading your workspace...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden dashboard-bg">
      <Sidebar />
      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden overflow-y-auto">
        <div className="w-full px-6 py-8 lg:px-12 xl:px-16">
          <DashboardContent>{children}</DashboardContent>
        </div>
      </main>
    </div>
  );
}
