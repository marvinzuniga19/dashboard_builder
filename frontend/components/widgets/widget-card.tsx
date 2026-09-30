"use client";

import { WIDGET_TYPE_LABELS, type Widget } from "@/types/api";

type WidgetCardProps = {
  widget: Widget;
  onRemove: (id: number, title: string) => void;
  isRemoving?: boolean;
};

export function WidgetCard({ widget, onRemove, isRemoving = false }: WidgetCardProps) {
  return (
    <div className="surface flex h-full w-full flex-col overflow-hidden bg-white shadow-xs transition-shadow hover:shadow-md">
      {/* Cabecera del widget con handle de arrastre */}
      <header className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
        <div className="flex items-center gap-2">
          {/* Grip handle para drag */}
          <button
            type="button"
            className="widget-drag-handle -ml-1 flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-hidden"
            title="Arrastrar para mover"
            aria-label="Arrastrar para mover widget"
          >
            <svg
              className="h-4 w-4"
              viewBox="0 0 16 16"
              fill="currentColor"
              aria-hidden="true"
            >
              <circle cx="5" cy="3.5" r="1.2" />
              <circle cx="11" cy="3.5" r="1.2" />
              <circle cx="5" cy="8" r="1.2" />
              <circle cx="11" cy="8" r="1.2" />
              <circle cx="5" cy="12.5" r="1.2" />
              <circle cx="11" cy="12.5" r="1.2" />
            </svg>
          </button>

          <span className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
            {WIDGET_TYPE_LABELS[widget.type]}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-slate-400">
            {widget.layout.w}×{widget.layout.h}
          </span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove(widget.id, widget.title);
            }}
            disabled={isRemoving}
            className="rounded-lg p-1 text-slate-400 transition hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
            title="Eliminar widget"
            aria-label={`Eliminar widget ${widget.title}`}
          >
            <svg
              className="h-4 w-4"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </header>

      {/* Contenido principal del widget */}
      <div className="flex min-h-0 flex-1 flex-col p-4">
        <h3 className="truncate font-semibold text-slate-900" title={widget.title}>
          {widget.title}
        </h3>

        <div className="mt-2 flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 p-4 text-center">
          {widget.type === "KPI" ? (
            <div className="space-y-1">
              <span className="text-3xl font-extrabold text-slate-800 tracking-tight">--</span>
              <p className="text-xs text-slate-500">
                {widget.configuration.metric ? `Métrica: ${widget.configuration.metric}` : "Sin datos asignados"}
              </p>
            </div>
          ) : (
            <div className="space-y-1 text-slate-400">
              <p className="text-xs font-medium text-slate-600">
                {widget.configuration.metric
                  ? `Métrica: ${widget.configuration.metric}`
                  : "Visualización en desarrollo"}
              </p>
              <p className="text-[11px] text-slate-400">
                {widget.type === "TABLE" ? "Estructura de tabla" : "Gráfico ECharts en FASE 6"}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Pie con coordenadas */}
      <footer className="flex items-center justify-between border-t border-slate-100 px-4 py-2 text-[11px] text-slate-400">
        <span>
          Pos: ({widget.layout.x}, {widget.layout.y})
        </span>
        <span>Redimensionable ↘</span>
      </footer>
    </div>
  );
}
