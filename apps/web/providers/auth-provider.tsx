"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api-client";
import { clearAuth, setOrgId, setTokens } from "@/lib/auth-storage";
import { ROUTES } from "@/lib/constants";
import type { AuthMeResponse, Organization, TokenResponse, User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  org: Organization | null;
  role: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, orgName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [org, setOrg] = useState<Organization | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshMe = useCallback(async () => {
    try {
      const me = await apiFetch<AuthMeResponse>("/auth/me");
      setUser(me.user);
      setOrg(me.current_org);
      setRole(me.role);
      if (me.current_org) setOrgId(me.current_org.id);
    } catch {
      setUser(null);
      setOrg(null);
      setRole(null);
    }
  }, []);

  useEffect(() => {
    refreshMe().finally(() => setLoading(false));
  }, [refreshMe]);

  const login = async (email: string, password: string) => {
    const tokens = await apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshMe();
    router.push(ROUTES.dashboard);
  };

  const register = async (email: string, password: string, name: string, orgName: string) => {
    const tokens = await apiFetch<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name, org_name: orgName }),
    });
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshMe();
    router.push(ROUTES.dashboard);
  };

  const logout = async () => {
    const refresh = typeof window !== "undefined" ? localStorage.getItem("katalyzu_refresh_token") : null;
    if (refresh) {
      try {
        await apiFetch("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refresh }) });
      } catch {
        /* ignore */
      }
    }
    clearAuth();
    setUser(null);
    setOrg(null);
    router.push(ROUTES.login);
  };

  return (
    <AuthContext.Provider value={{ user, org, role, loading, login, register, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
