import { API_URL } from "./constants";
import { clearAuth, getAccessToken, getOrgId, getRefreshToken, setTokens } from "./auth-storage";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
  ) {
    super(message);
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!res.ok) {
    clearAuth();
    return null;
  }

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  let token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const orgId = getOrgId();
  if (orgId) headers.set("X-Org-Id", orgId);

  let res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && getRefreshToken()) {
    token = await refreshAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
      res = await fetch(`${API_URL}${path}`, { ...options, headers });
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail || err.error?.message || res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const orgId = getOrgId();
  if (orgId) headers.set("X-Org-Id", orgId);

  const res = await fetch(`${API_URL}${path}`, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail || res.statusText);
  }
  return res.json();
}
