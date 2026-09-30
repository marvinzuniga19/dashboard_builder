import type { ApiErrorResponse } from "@/types/api";

const baseUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

// PUT no se incluye a propósito: el backend no lo declara en `allow_methods`, así
// que un PUT cruzando orígenes fallaría en el preflight sin aviso.
type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
};

async function toApiError(response: Response): Promise<ApiError> {
  const fallback = `La API respondió con estado ${response.status}.`;
  try {
    const payload = (await response.json()) as Partial<ApiErrorResponse>;
    const detail = payload.detail;
    if (detail && typeof detail === "object") {
      return new ApiError(response.status, detail.code ?? "API_ERROR", detail.message ?? fallback);
    }
  } catch {
    // Respuesta sin JSON (por ejemplo, un error del proxy).
  }
  return new ApiError(response.status, "API_ERROR", fallback);
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    // La sesión viaja en una cookie httpOnly gestionada por el navegador.
    credentials: "include",
    cache: "no-store",
    signal,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { signal });
}

export function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { method: "POST", body, signal });
}

export function apiPatch<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { method: "PATCH", body, signal });
}

/** DELETE devuelve 204 sin cuerpo: apiRequest ya resuelve ese caso a `undefined`. */
export function apiDelete<T = void>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { method: "DELETE", signal });
}

export function apiUrl(path: string): string {
  return `${baseUrl}${path}`;
}
