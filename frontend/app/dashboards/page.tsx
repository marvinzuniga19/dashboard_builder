"use client";

import { ArrowUpRight, LayoutDashboard, Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { useDashboardActions, useDashboards } from "@/hooks/useDashboards";

export default function DashboardsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <DashboardsContent />
      </AppShell>
    </RequireAuth>
  );
}

function DashboardsContent() {
  const router = useRouter();
  const list = useDashboards();
  const actions = useDashboardActions();
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const created = await actions.create({ name, description: description || null });
    if (created) {
      setName("");
      setDescription("");
      setIsCreating(false);
      router.push(`/dashboards/${created.id}`);
    }
  }

  async function handleRemove(id: number, dashboardName: string) {
    if (!window.confirm(`¿Eliminar «${dashboardName}»? Esta acción no se puede deshacer.`)) {
      return;
    }
    await actions.remove(id);
  }

  return (
    <main className="ui-page space-y-7">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="ui-eyebrow">
            Tu espacio de trabajo
          </p>
          <h1 className="ui-heading">Dashboards</h1>
          <p className="ui-subtitle max-w-xl">
            Tus espacios de análisis. Organiza gráficos e indicadores y encuentra lo que necesitas de un vistazo.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsCreating((value) => !value)}
          aria-expanded={isCreating}
          className="ui-button ui-button-primary"
        >
          <Plus size={16} aria-hidden="true" />{isCreating ? "Cancelar" : "Nuevo dashboard"}
        </button>
      </section>

      {isCreating ? (
        <form onSubmit={handleCreate} className="surface space-y-4 p-6" noValidate>
          <div className="space-y-2">
            <label htmlFor="dashboard-name" className="block text-sm font-semibold text-slate-700">
              Nombre
            </label>
            <input
              id="dashboard-name"
              name="name"
              required
              maxLength={120}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Ventas mensuales"
              aria-describedby={actions.error ? "dashboard-create-error" : undefined}
              className="ui-input"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="dashboard-description"
              className="block text-sm font-semibold text-slate-700"
            >
              Descripción <span className="font-normal text-slate-400">(opcional)</span>
            </label>
            <textarea
              id="dashboard-description"
              name="description"
              rows={3}
              maxLength={1000}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Qué contiene este dashboard."
              className="ui-input"
            />
          </div>
          {actions.error ? (
            <p
              id="dashboard-create-error"
              role="alert"
              className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            >
              {actions.error}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={actions.isSubmitting || name.trim() === ""}
            className="ui-button ui-button-primary"
          >
            {actions.isSubmitting ? "Creando…" : "Crear dashboard"}
          </button>
        </form>
      ) : null}

      {list.state === "error" ? (
        <section className="surface p-7" role="alert">
          <h2 className="text-lg font-bold">No se pudieron cargar los dashboards</h2>
          <p className="mt-2 text-sm text-slate-500">{list.error}</p>
        </section>
      ) : null}

      {list.state === "empty" ? (
        <section className="surface p-7">
          <h2 className="text-lg font-bold">Todavía no tienes dashboards</h2>
          <p className="mt-2 text-sm text-slate-500">
            Crea el primero con el botón «Nuevo dashboard».
          </p>
        </section>
      ) : null}

      {list.state === "outOfRange" ? (
        <section className="surface p-7">
          <h2 className="text-lg font-bold">Esta página ya no tiene dashboards</h2>
          <p className="mt-2 text-sm text-slate-500">
            Borraste los últimos dashboards de esta página. Tienes {list.total} en total.
          </p>
          <button
            type="button"
            onClick={() => list.goToPage(list.pageCount)}
            className="mt-5 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800"
          >
            Volver a la página {list.pageCount}
          </button>
        </section>
      ) : null}

      {list.state === "loading" ? (
        <section className="surface p-7">
          <p className="text-sm text-slate-500" aria-live="polite">
            Cargando dashboards…
          </p>
        </section>
      ) : null}

      {list.state === "success" ? (
        <section aria-label="Lista de dashboards">
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {list.dashboards.map((dashboard) => (
              <li key={dashboard.id} className="surface flex min-w-0 flex-col p-5 transition-shadow hover:shadow-md">
                <div className="mb-5 flex items-center justify-between text-slate-400"><span className="rounded-lg bg-teal-50 p-2 text-teal-800"><LayoutDashboard size={18} aria-hidden="true" /></span><ArrowUpRight size={17} aria-hidden="true" /></div>
                <Link
                  href={`/dashboards/${dashboard.id}`}
                  className="break-words text-base font-semibold hover:text-teal-800"
                >
                  {dashboard.name}
                </Link>
                <p className="mt-2 flex-1 break-words text-sm leading-6 text-slate-500">
                  {dashboard.description || (
                    <span className="text-slate-400">Sin descripción</span>
                  )}
                </p>
                <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                  <span className="text-xs text-slate-400">
                    Actualizado el {formatDate(dashboard.updated_at)}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemove(dashboard.id, dashboard.name)}
                    className="text-xs font-semibold text-slate-500 transition hover:text-red-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800"
                  >
                    Eliminar
                  </button>
                </div>
              </li>
            ))}
          </ul>

          {list.pageCount > 1 ? (
            <nav
              className="mt-6 flex items-center justify-between"
              aria-label="Paginación de dashboards"
            >
              <button
                type="button"
                onClick={() => list.goToPage(list.page - 1)}
                disabled={!list.hasPrevious}
                className="ui-button"
              >
                Anterior
              </button>
              <span aria-live="polite" className="text-sm text-slate-500">
                Página {list.page} de {list.pageCount} · {list.total} dashboards
              </span>
              <button
                type="button"
                onClick={() => list.goToPage(list.page + 1)}
                disabled={!list.hasNext}
                className="ui-button"
              >
                Siguiente
              </button>
            </nav>
          ) : null}
        </section>
      ) : null}

      {actions.error && !isCreating ? (
        <p role="alert" className="text-sm text-red-700">
          {actions.error}
        </p>
      ) : null}
    </main>
  );
}

function formatDate(value: string): string {
  // SQLite devuelve fechas sin zona horaria; se interpretan como hora local.
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" });
}
