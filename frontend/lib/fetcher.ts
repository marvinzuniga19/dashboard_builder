import { apiRequest, ApiError } from "@/lib/api";

/** Fetcher único de SWR: propaga ApiError para que los hooks distingan 401 de otros fallos. */
export function fetcher<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}
