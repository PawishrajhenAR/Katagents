export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const ROUTES = {
  login: "/login",
  signup: "/signup",
  dashboard: "/dashboard",
  campaigns: "/dashboard/campaigns",
  agents: "/dashboard/agents",
  analytics: "/dashboard/analytics",
  settings: "/dashboard/settings",
} as const;
