"use client";

import { ArrowLeft, Check, Eye, MoreHorizontal, Pencil, Plus, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { DashboardGrid } from "@/components/dashboard/dashboard-grid";
import { RequireAuth } from "@/components/require-auth";
import { useDashboard, useDashboardActions } from "@/hooks/useDashboards";
import { useWidgetActions, useWidgets } from "@/hooks/useWidgets";
import type { WidgetLayoutItem } from "@/types/api";
import { WIDGET_TYPES, WIDGET_TYPE_LABELS, type WidgetType } from "@/types/api";

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
  const [isEditing, setIsEditing] = useState(false);
  const [showWidgetForm, setShowWidgetForm] = useState(false);
  const [name, setName] = useState<string | null>(null);
  const widgets = useWidgets(dashboard ? dashboard.id : null);
  const widgetActions = useWidgetActions(dashboard ? dashboard.id : null);
  const [tipoWidget, setTipoWidget] = useState<WidgetType>("KPI");
  const [tituloWidget, setTituloWidget] = useState("");

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

  async function handleCreateWidget(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const creado = await widgetActions.create({
      type: tipoWidget,
      title: tituloWidget.trim() || undefined,
    });
    if (creado) {
      setTituloWidget("");
      setShowWidgetForm(false);
    }
  }

  async function handleRemoveWidget(id: number, title: string) {
    if (!window.confirm(`¿Eliminar el widget «${title}»?`)) {
      return;
    }
    await widgetActions.remove(id);
  }

  const handleLayoutChange = useCallback(
    (items: WidgetLayoutItem[]) => {
      void widgetActions.updateLayouts(items);
    },
    [widgetActions],
  );

  if (!esValido) {
    return <Mensaje titulo="Identificador no válido" detalle="La ruta no contiene un id de dashboard." />;
  }

  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-10 lg:px-10 lg:py-12">
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
      <main className="mx-auto max-w-7xl px-6 py-10 lg:px-10 lg:py-12">
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
    <main className="ui-page">
      <Link
        href="/dashboards"
        className="mb-6 inline-flex items-center gap-2 text-xs text-slate-500 hover:text-teal-800"
      >
        <ArrowLeft size={14} aria-hidden="true" /> Volver a dashboards
      </Link>

      <section className="flex flex-wrap items-center justify-between gap-5">
        <div className="min-w-0 flex-1">
          <p className="ui-eyebrow">Mi dashboard</p>
          <h1 className="ui-heading">{dashboard.name}</h1>
          <p className="ui-subtitle">{dashboard.description || "Organiza tus indicadores y gráficos en un solo lugar."}</p>
        </div>
        <div className="dashboard-actions">
          <button type="button" className="ui-button" aria-pressed={isEditing} disabled={widgetActions.isSubmitting}
            onClick={() => { setIsEditing((value) => !value); setShowWidgetForm(false); setName(null); }}>
            {isEditing ? <Check size={15} aria-hidden="true" /> : <Pencil size={15} aria-hidden="true" />}
            {isEditing ? "Terminar edición" : "Editar"}
          </button>
          <button type="button" className="ui-button ui-button-primary" aria-expanded={showWidgetForm} aria-controls="widget-create-panel"
            onClick={() => { setIsEditing(true); setShowWidgetForm((value) => !value); }}>
            <Plus size={16} aria-hidden="true" /> Añadir widget
          </button>
          <details className="dashboard-options">
            <summary className="ui-button" aria-label="Opciones del dashboard"><MoreHorizontal size={17} aria-hidden="true" /></summary>
            <div className="dashboard-option-menu"><button type="button" className="ui-danger" onClick={handleRemove} disabled={actions.isSubmitting}>
              <Trash2 size={14} aria-hidden="true" /> Eliminar dashboard
            </button></div>
          </details>
        </div>
      </section>

      {/* Renombrar */}
      {isEditing ? (
      <details className="surface edit-properties">
        <summary>Propiedades del dashboard</summary>
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
            className="ui-input flex-1"
          />
          <button
            type="submit"
            disabled={actions.isSubmitting || name === null || name.trim() === ""}
            className="ui-button ui-button-primary"
          >
            {actions.isSubmitting ? "Guardando…" : "Guardar"}
          </button>
          {name !== null && name !== dashboard.name ? (
            <button
              type="button"
              onClick={() => setName(null)}
              className="ui-button"
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
      </details>
      ) : null}
      {actions.error && !isEditing ? <p role="alert" className="mt-4 text-sm text-red-700">{actions.error}</p> : null}

      {showWidgetForm ? (
      <section id="widget-create-panel" className="surface widget-create-panel" aria-label="Crear widget">
        <div className="flex items-center justify-between gap-3"><h2 className="text-sm font-semibold">Nuevo widget</h2>
          <button type="button" className="ui-icon-button" aria-label="Cerrar formulario de widget" onClick={() => setShowWidgetForm(false)}><X size={16} aria-hidden="true" /></button>
        </div>
        <form
          onSubmit={handleCreateWidget}
          className="widget-create-form"
          noValidate
        >
          <div className="flex flex-col gap-2">
            <label htmlFor="widget-type" className="text-sm font-semibold text-slate-700">
              Tipo
            </label>
            <select
              id="widget-type"
              name="type"
              value={tipoWidget}
              onChange={(event) => setTipoWidget(event.target.value as WidgetType)}
              className="ui-input"
            >
              {WIDGET_TYPES.map((tipo) => (
                <option key={tipo} value={tipo}>
                  {WIDGET_TYPE_LABELS[tipo]}
                </option>
              ))}
            </select>
          </div>

          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <label htmlFor="widget-title" className="text-sm font-semibold text-slate-700">
              Título <span className="font-normal text-slate-400">(opcional)</span>
            </label>
            <input
              id="widget-title"
              name="title"
              maxLength={120}
              value={tituloWidget}
              onChange={(event) => setTituloWidget(event.target.value)}
              placeholder="Si se deja vacío se usa el nombre del tipo"
              aria-describedby={widgetActions.error ? "widget-create-error" : undefined}
              className="ui-input"
            />
          </div>

          <button
            type="submit"
            disabled={widgetActions.isSubmitting}
            className="ui-button ui-button-primary"
          >
            {widgetActions.isSubmitting ? "Añadiendo…" : "Crear widget"}
          </button>

          {widgetActions.error ? (
            <p
              id="widget-create-error"
              role="alert"
              className="col-span-full rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            >
              {widgetActions.error}
            </p>
          ) : null}
        </form>
      </section>
      ) : null}
      {widgetActions.error && !showWidgetForm ? <p role="alert" className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{widgetActions.error}</p> : null}
      <div className="dashboard-toolbar">
        <span>{widgets.widgets.length} {widgets.widgets.length === 1 ? "widget" : "widgets"}</span>
        <span className="inline-flex items-center gap-2" role="status">{isEditing ? <Pencil size={13} aria-hidden="true" /> : <Eye size={14} aria-hidden="true" />}
          {widgetActions.isSubmitting ? "Guardando…" : isEditing ? "Modo de edición · Los cambios se guardan al soltar" : "Vista de lectura"}
        </span>
      </div>

      {/* Lienzo del grid */}
      <section aria-label="Lienzo del dashboard">
        {widgets.state === "loading" ? (
          <p className="text-sm text-slate-500" aria-live="polite">
            Cargando widgets…
          </p>
        ) : null}

        {widgets.state === "error" ? (
          <section className="surface p-7" role="alert">
            <h3 className="text-lg font-bold">No se pudieron cargar los widgets</h3>
            <p className="mt-2 text-sm text-slate-500">{widgets.error}</p>
          </section>
        ) : null}

        {widgets.state === "empty" ? (
          <section className="surface p-7">
            <h3 className="text-lg font-bold">Este dashboard está vacío</h3>
            <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
              Empieza con «Añadir widget». Usa el modo de edición para mover y redimensionar tus gráficos.
            </p>
          </section>
        ) : null}

        {widgets.state === "success" ? (
          <DashboardGrid
            widgets={widgets.widgets}
            onRemoveWidget={handleRemoveWidget}
            onLayoutChange={handleLayoutChange}
            isSubmitting={widgetActions.isSubmitting}
            isEditing={isEditing}
          />
        ) : null}
      </section>
    </main>
  );
}

function Mensaje({ titulo, detalle }: { titulo: string; detalle: string }) {
  return (
    <main className="mx-auto max-w-7xl px-6 py-10 lg:px-10 lg:py-12">
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
