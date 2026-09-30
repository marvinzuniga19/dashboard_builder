"use client";

import { useCallback, useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { ApiError, apiDelete, apiPatch, apiPost } from "@/lib/api";
import { PAGE_SIZE, resolveListPage, type ListState } from "@/lib/dashboard-pagination";
import type { Dashboard, DashboardCreate, DashboardPage, DashboardUpdate } from "@/types/api";

const LIST_KEY_PREFIX = "/dashboards?";

export type DashboardsState = ListState;

export type DashboardsResult = {
  dashboards: Dashboard[];
  total: number;
  page: number;
  pageCount: number;
  hasPrevious: boolean;
  hasNext: boolean;
  state: DashboardsState;
  error: string | null;
  goToPage: (page: number) => void;
};

function messageFor(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback;
}

export function useDashboards(): DashboardsResult {
  const [offset, setOffset] = useState(0);
  const { data, error, isLoading } = useSWR<DashboardPage>(
    `${LIST_KEY_PREFIX}limit=${PAGE_SIZE}&offset=${offset}`,
  );

  const total = data?.total ?? 0;
  const view = resolveListPage({
    total,
    offset,
    pageSize: PAGE_SIZE,
    isPending: isLoading || data === undefined,
    hasError: Boolean(error),
  });

  return {
    dashboards: data?.items ?? [],
    total,
    page: view.page,
    pageCount: view.pageCount,
    hasPrevious: view.hasPrevious,
    hasNext: view.hasNext,
    state: view.state,
    error: error ? messageFor(error, "No se pudo cargar la lista de dashboards.") : null,
    goToPage: (page: number) => setOffset(Math.max(0, (page - 1) * PAGE_SIZE)),
  };
}

/**
 * Un dashboard concreto. `notFound` distingue "no existe o no es tuyo" de un
 * fallo de red, para que la página pueda ofrecer reintentar en un caso y no en
 * el otro.
 */
export function useDashboard(id: number | null) {
  const { data, error, isLoading, mutate } = useSWR<Dashboard>(
    id === null ? null : `/dashboards/${id}`,
  );

  return {
    dashboard: data ?? null,
    isLoading,
    error: error ? messageFor(error, "No se pudo cargar el dashboard.") : null,
    notFound: error instanceof ApiError && error.status === 404,
    reload: mutate,
  };
}

export type DashboardActions = {
  create: (payload: DashboardCreate) => Promise<Dashboard | null>;
  update: (id: number, payload: DashboardUpdate) => Promise<Dashboard | null>;
  /** `null` cuando la llamada falla; el motivo queda en `error`. */
  remove: (id: number) => Promise<boolean | null>;
  error: string | null;
  isSubmitting: boolean;
  clearError: () => void;
};

/**
 * Mutaciones de dashboard. Tras cada una se revalida el listado: sin esto, crear
 * o renombrar dejaría la lista mostrando datos obsoletos.
 */
export function useDashboardActions(): DashboardActions {
  const { mutate } = useSWRConfig();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const run = useCallback(async <T,>(
    action: () => Promise<T>,
    fallbackMessage: string,
    onSuccess?: () => void,
  ): Promise<T | null> => {
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await action();
      onSuccess?.();
      return result;
    } catch (caught) {
      setError(messageFor(caught, fallbackMessage));
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const create = useCallback(
    (payload: DashboardCreate) =>
      run(
        () => apiPost<Dashboard>("/dashboards", payload),
        "No se pudo crear el dashboard.",
        // El filtro alcanza todas las páginas del listado, no solo la visible.
        () => void mutate((key) => typeof key === "string" && key.startsWith(LIST_KEY_PREFIX)),
      ),
    [run, mutate],
  );

  const update = useCallback(
    (id: number, payload: DashboardUpdate) =>
      run(
        () => apiPatch<Dashboard>(`/dashboards/${id}`, payload),
        "No se pudo guardar el dashboard.",
        () => {
          void mutate((key) => typeof key === "string" && key.startsWith(LIST_KEY_PREFIX));
          void mutate(`/dashboards/${id}`);
        },
      ),
    [run, mutate],
  );

  const remove = useCallback(
    (id: number) =>
      run(async () => {
        await apiDelete(`/dashboards/${id}`);
        return true;
      }, "No se pudo eliminar el dashboard.", () =>
        void mutate((key) => typeof key === "string" && key.startsWith(LIST_KEY_PREFIX)),
      ),
    [run, mutate],
  );

  return { create, update, remove, error, isSubmitting, clearError: () => setError(null) };
}