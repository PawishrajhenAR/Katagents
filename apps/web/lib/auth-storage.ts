const ACCESS_KEY = "katalyzu_access_token";
const REFRESH_KEY = "katalyzu_refresh_token";
const ORG_KEY = "katalyzu_org_id";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function getOrgId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ORG_KEY);
}

export function setTokens(access: string, refresh: string, orgId?: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  if (orgId) localStorage.setItem(ORG_KEY, orgId);
}

export function setOrgId(orgId: string) {
  localStorage.setItem(ORG_KEY, orgId);
}

export function clearAuth() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(ORG_KEY);
}
