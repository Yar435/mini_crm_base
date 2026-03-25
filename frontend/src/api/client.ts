const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_KEY);
}

export function setTokens(access: string, refresh: string): void {
  sessionStorage.setItem(ACCESS_KEY, access);
  sessionStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}

type ApiErrorBody = { detail?: string; [key: string]: unknown };

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

const API_PREFIX = "/api";

function joinPath(path: string): string {
  if (path.startsWith("http")) return path;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_PREFIX}${p}`;
}

export async function apiFetch(
  path: string,
  init: RequestInit & { skipAuth?: boolean } = {}
): Promise<Response> {
  const { skipAuth, headers: hdrs, ...rest } = init;
  const headers = new Headers(hdrs);
  if (!headers.has("Content-Type") && rest.body && !(rest.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (!skipAuth && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(joinPath(path), { ...rest, headers });
  return res;
}

export async function apiJson<T>(path: string, init?: RequestInit & { skipAuth?: boolean }): Promise<T> {
  const res = await apiFetch(path, init);
  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const msg =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as ApiErrorBody).detail)
        : res.statusText;
    throw new ApiError(msg || `HTTP ${res.status}`, res.status, data);
  }

  return data as T;
}
