"use client";

import { useCallback, useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { ApiError, apiDelete, apiPatch, apiPost, apiPut } from "@/lib/api";
import type { Widget, WidgetCreate, WidgetLayoutItem, WidgetUpdate } from "@/types/api";

// Un prefijo por dashboard: cada lienzo tiene su propia clave y las revalidaciones
// en masa solo alcanzan las de widgets.
const LIST_KEY_PREFIX = "/dashboards/";

export type WidgetsState = "loading" | "success" | "empty" | "error";

export type WidgetsResult = {
  widgets: Widget[];
  state: WidgetsState;
  error: string | null;
};

export type WidgetActions = {
  create: (payload: WidgetCreate) => Promise<Widget | null>;
  update: (id: number, payload: WidgetUpdate) => Promise<Widget | null>;
  updateLayouts: (items: WidgetLayoutItem[]) => Promise<Widget[] | null>;
  /** `null` cuando la llamada falla; el motivo queda en `error`. */
  remove: (id: number) => Promise<boolean | null>;
  error: string | null;
  isSubmitting: boolean;
  clearError: () => void;
};

function messageFor(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback;
}

function listKey(dashboardId: number | null): string | null {
  return dashboardId === null ? null : `${LIST_KEY_PREFIX}${dashboardId}/widgets`;
}

/** Los widgets de un dashboard. `dashboardId` a null evita la petición. */
export function useWidgets(dashboardId: number | null): WidgetsResult {
  const { data, error, isLoading } = useSWR<Widget[]>(listKey(dashboardId));

  let state: WidgetsState = "loading";
  if (error) {
    state = "error";
  } else if (!isLoading && data) {
    state = data.length === 0 ? "empty" : "success";
  }

  return {
    widgets: data ?? [],
    state,
    error: error ? messageFor(error, "No se pudieron cargar los widgets.") : null,
  };
}

/**
 * Mutaciones de widgets. Tras cada una se revalida el listado del dashboard, para
 * que el lienzo no se quede mostrando lo que había antes del cambio.
 */
export function useWidgetActions(dashboardId: number | null): WidgetActions {
  const { mutate } = useSWRConfig();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const revalidarLista = useCallback(
    () => void mutate(listKey(dashboardId)),
    [mutate, dashboardId],
  );

  const run = useCallback(
    async <T,>(
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
    },
    [],
  );

  const create = useCallback(
    (payload: WidgetCreate) =>
      run(
        // El dashboard sale del hook: nunca se crea en uno distinto del que luego
        // se revalida.
        () => apiPost<Widget>(`/dashboards/${dashboardId}/widgets`, payload),
        "No se pudo crear el widget.",
        revalidarLista,
      ),
    [run, revalidarLista, dashboardId],
  );

  const update = useCallback(
    (id: number, payload: WidgetUpdate) =>
      run(() => apiPatch<Widget>(`/widgets/${id}`, payload), "No se pudo guardar el widget.", revalidarLista),
    [run, revalidarLista],
  );

  const updateLayouts = useCallback(
    (items: WidgetLayoutItem[]) => {
      if (dashboardId === null) return Promise.resolve(null);
      // Actualización optimista de SWR para fluidez inmediata
      void mutate(
        listKey(dashboardId),
        (current: Widget[] | undefined) => {
          if (!current) return current;
          const map = new Map(items.map((it) => [it.id, it]));
          return current.map((w) => {
            const item = map.get(w.id);
            return item ? { ...w, layout: { x: item.x, y: item.y, w: item.w, h: item.h } } : w;
          });
        },
        false,
      );

      return run(
        () => apiPut<Widget[]>(`/dashboards/${dashboardId}/layouts`, { items }),
        "No se pudo guardar la posición de los widgets.",
        revalidarLista,
      );
    },
    [dashboardId, mutate, run, revalidarLista],
  );

  const remove = useCallback(
    (id: number) =>
      run(
        async () => {
          await apiDelete(`/widgets/${id}`);
          return true;
        },
        "No se pudo eliminar el widget.",
        revalidarLista,
      ),
    [run, revalidarLista],
  );

  return { create, update, updateLayouts, remove, error, isSubmitting, clearError: () => setError(null) };
}

