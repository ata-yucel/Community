// Tek merkezden HTTP: ekranlar fetch yerine apiFetch kullanır.
//
// auth ayrımı YAPISALDIR (URL karşılaştırması yok):
// - auth: true  -> istek token'la gider; 401 dönerse oturum ölmüş demektir
//                  (refresh token yok) ve global çıkış tetiklenir.
// - auth: false -> token eklenmez; 401'i çağıran ekran yorumlar
//                  (örn. login formu "e-posta veya şifre hatalı" gösterir).

const BASE_URL = process.env.EXPO_PUBLIC_API_URL;

export class ApiError extends Error {
  status: number;

  constructor(status: number) {
    super(`HTTP ${status}`);
    this.status = status;
  }
}

// auth-context bu ikisini uygulama açılırken bağlar; api.ts hiçbir
// React/depolama detayı bilmez.
let authToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler;
}

type ApiOptions = {
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  auth?: boolean;
};

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  if (!BASE_URL) {
    throw new Error("EXPO_PUBLIC_API_URL tanımsız — frontend/.env dosyasını kontrol et");
  }
  const { method = "GET", body, auth = false } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && authToken) headers["Authorization"] = `Bearer ${authToken}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth) {
    onUnauthorized?.();
  }
  if (!response.ok) {
    throw new ApiError(response.status);
  }
  return (await response.json()) as T;
}
