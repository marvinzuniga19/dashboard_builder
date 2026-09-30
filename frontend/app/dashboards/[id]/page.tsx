"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { useDashboard, useDashboardActions } from "@/hooks/useDashboards";

export default function DashboardDetailPage() {
  return (
    <RequireAuth>
      <AppShell>
        <DashboardDetail />
      </AppShell>
    </RequireAuth>
  );
}

function DashboardDetail() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const dashboardId = Number.parseInt(params.id, 10);
  const esValido = Number.isInteger(dashboardId) && dashboardId > 0;

  const { dashboard, isLoading, error, notFound, reload } = useDashboard(
    esValido ? dashboardId : null,
  );
  const actions = useDashboardActions();
  const [name, setName] = useState<string | null>(null);

  async function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dashboard || name === null) return;
    await actions.update(dashboard.id, { name });
    await reload();
  }

  async function handleRemove() {
    if (!dashboard) return;
    if (!window.confirm(`¿Eliminar «${dashboard.name}»? Esta acción no se puede deshacer.`)) {
      return;
    }
    const eliminado = await actions.remove(dashboard.id);
    if (eliminado) {
      router.replace("/dashboards");
    }
  }

  if (!esValido) {
    return <Mensaje titulo="Identificador no válido" detalle="La ruta no contiene un id de dashboard." />;
  }

  if (isLoading) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10 lg:px-10 lg:py-12">
        <p className="text-sm text-slate-500" aria-live="polite">
          Cargando dashboard…
        </p>
      </main>
    );
  }

  if (notFound) {
    return (
      <Mensaje
        titulo="Dashboard no encontrado"
        detalle="No existe o no pertenece a tu cuenta."
      />
    );
  }

  if (error || !dashboard) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10 lg:px-10 lg:py-12">
        <section className="surface p-7" role="alert">
          <h1 className="text-lg font-bold">No se pudo cargar el dashboard</h1>
          <p className="mt-2 text-sm text-slate-500">{error}</p>
          <button
            type="button"
            onClick={() => void reload()}
            className="mt-5 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold transition hover:bg-slate-50"
          >
            Reintentar
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl space-y-7 px-6 py-10 lg:px-10 lg:py-12">
      <Link
        href="/dashboards"
        className="inline-block text-sm font-semibold text-slate-500 transition hover:text-teal-800"
      >
        ← Volver a dashboards
      </Link>

      <section className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-700">
            Dashboard
          </p>
          <h1 className="mt-3 truncate text-3xl font-bold tracking-tight sm:text-4xl">
            {dashboard.name}
          </h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">
            {dashboard.description || <span className="text-slate-400">Sin descripción</span>}
          </p>
        </div>
        <button
          type="button"
          onClick={handleRemove}
          disabled={actions.isSubmitting}
          className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:border-red-200 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Eliminar
        </button>
      </section>

      <section className="surface p-6">
        <h2 className="text-sm font-semibold text-slate-700">Renombrar</h2>
        <form onSubmit={handleSave} className="mt-3 flex flex-wrap gap-3" noValidate>
          <label htmlFor="dashboard-rename" className="sr-only">
            Nuevo nombre
          </label>
          <input
            id="dashboard-rename"
            name="name"
            required
            maxLength={120}
            value={name ?? dashboard.name}
            onChange={(event) => setName(event.target.value)}
            className="min-w-0 flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-4 focus:ring-teal-100"
          />
          <button
            type="submit"
            disabled={actions.isSubmitting || name === null || name.trim() === ""}
            className="rounded-xl bg-teal-800 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-900 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {actions.isSubmitting ? "Guardando…" : "Guardar"}
          </button>
          {name !== null && name !== dashboard.name ? (
            <button
              type="button"
              onClick={() => setName(null)}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
            >
              Cancelar
            </button>
          ) : null}
        </form>
        {actions.error ? (
          <p role="alert" className="mt-3 text-sm text-red-700">
            {actions.error}
          </p>
        ) : null}
      </section>

      {/* El lienzo del dashboard se monta en la FASE 5 con react-grid-layout. */}
      <section className="surface flex min-h-64 flex-col items-center justify-center p-10 text-center">
        <h2 className="text-lg font-bold">Este dashboard está vacío</h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
          Los widgets con métricas y gráficos se añaden en las próximas fases. El nombre y la
          descripción ya se guardan.
        </p>
      </section>
    </main>
  );
}

function Mensaje({ titulo, detalle }: { titulo: string; detalle: string }) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10 lg:px-10 lg:py-12">
      <section className="surface p-7">
        <h1 className="text-lg font-bold">{titulo}</h1>
        <p className="mt-2 text-sm text-slate-500">{detalle}</p>
        <Link
          href="/dashboards"
          className="mt-5 inline-block rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold transition hover:bg-slate-50"
        >
          Volver a dashboards
        </Link>
      </section>
    </main>
  );
}
