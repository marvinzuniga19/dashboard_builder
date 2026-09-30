"use client";

import { useCallback, useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { ApiError, apiPost } from "@/lib/api";
import { isUnauthorized } from "@/lib/fetcher";
import type { User } from "@/types/api";

const SESSION_KEY = "/auth/me";

export type SessionState = "loading" | "authenticated" | "unauthenticated" | "error";

export type Session = {
  state: SessionState;
  user: User | null;
  /** Mensaje de la API cuando el fallo no es una sesión ausente. */
  error: string | null;
};

export function useSession(): Session {
  const { data, error, isLoading } = useSWR<User>(SESSION_KEY, {
    revalidateOnFocus: true,
  });

  if (error) {
    return {
      state: isUnauthorized(error) ? "unauthenticated" : "error",
      user: null,
      error: isUnauthorized(error) ? null : (error as ApiError).message,
    };
  }
  if (isLoading || data === undefined) {
    return { state: "loading", user: null, error: null };
  }
  return { state: "authenticated", user: data, error: null };
}

export type LoginCredentials = { email: string; password: string };

export function useLogin() {
  const { mutate } = useSWRConfig();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsSubmitting(true);
      setError(null);
      try {
        const user = await apiPost<User>("/auth/login", credentials);
        await mutate(SESSION_KEY, user, { revalidate: false });
        return user;
      } catch (caught) {
        const message =
          caught instanceof ApiError
            ? caught.message
            : "No se pudo conectar con la API. Comprueba que el backend esté activo.";
        setError(message);
        return null;
      } finally {
        setIsSubmitting(false);
      }
    },
    [mutate],
  );

  return { login, error, isSubmitting };
}

export function useLogout() {
  const { mutate } = useSWRConfig();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const logout = useCallback(async () => {
    setIsSubmitting(true);
    try {
      await apiPost<{ message: string }>("/auth/logout", {});
      await mutate(SESSION_KEY, undefined, { revalidate: false });
    } finally {
      setIsSubmitting(false);
    }
  }, [mutate]);

  return { logout, isSubmitting };
}
