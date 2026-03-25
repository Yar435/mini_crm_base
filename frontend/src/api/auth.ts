import { apiJson, clearTokens, setTokens } from "./client";

export type TokenPair = {
  access: string;
  refresh: string;
};

type TokenResponse = {
  access: string;
  refresh: string;
};

export async function login(username: string, password: string): Promise<TokenPair> {
  const data = await apiJson<TokenResponse>("/auth/token/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ username, password }),
  });
  setTokens(data.access, data.refresh);
  return { access: data.access, refresh: data.refresh };
}

export function logout(): void {
  clearTokens();
}
