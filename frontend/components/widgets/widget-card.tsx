"use client";

import { BarChart3, CircleGauge, GripVertical, LineChart, PieChart, Table2, Trash2 } from "lucide-react";
import { ChartRenderer } from "@/components/charts/ChartRenderer";
import { CHART_DEMO_DATA } from "@/lib/chart-demo-data";
import { isChartType } from "@/types/charts";
import { WIDGET_TYPE_LABELS, type Widget, type WidgetType } from "@/types/api";

const TYPE_ICONS = { KPI: CircleGauge, BAR_CHART: BarChart3, LINE_CHART: LineChart, PIE_CHART: PieChart, TABLE: Table2 } satisfies Record<WidgetType, typeof CircleGauge>;

type WidgetCardProps = {
  widget: Widget;
  onRemove: (id: number, title: string) => void;
  isRemoving?: boolean;
  isEditing?: boolean;
};

export function WidgetCard({ widget, onRemove, isRemoving = false, isEditing = false }: WidgetCardProps) {
  const Icon = TYPE_ICONS[widget.type];
  return (
    <article className={`widget-card ${isEditing ? "is-editing" : ""}`}>
      <header className="widget-header">
        <div className="flex min-w-0 items-center gap-2">
          {isEditing ? <button type="button" disabled={isRemoving} className="widget-drag-handle ui-icon-button" aria-label="Arrastrar para mover widget"><GripVertical size={16} aria-hidden="true" /></button> : null}
          <div className="min-w-0"><h3 className="truncate text-sm font-semibold" title={widget.title}>{widget.title}</h3>
            <span className="widget-type"><Icon size={12} aria-hidden="true" />{WIDGET_TYPE_LABELS[widget.type]}</span></div>
        </div>
        {isEditing ? <button type="button" onClick={(event) => { event.stopPropagation(); onRemove(widget.id, widget.title); }} disabled={isRemoving}
          className="ui-icon-button widget-delete" aria-label={`Eliminar widget ${widget.title}`}><Trash2 size={15} aria-hidden="true" /></button> : null}
      </header>
      <div className="widget-body">
        {isChartType(widget.type) ? (
          <div className="flex min-h-[166px] flex-1 flex-col">
            <p className="widget-demo">Datos de demostración · Sin fuente conectada</p>
            <div className="min-h-[140px] flex-1"><ChartRenderer type={widget.type} data={CHART_DEMO_DATA[widget.type]} title={`${widget.title} (datos de demostración)`} /></div>
          </div>
        ) : (
          <div className="widget-empty">
            <Icon size={24} strokeWidth={1.5} aria-hidden="true" />
            {widget.type === "KPI" ? <span className="text-3xl font-semibold tracking-tight">—</span> : null}
            <p className="text-sm">{widget.configuration.metric ? `Métrica: ${widget.configuration.metric}` : "Sin datos asignados"}</p>
            <p className="text-xs text-slate-500">Conecta una fuente para visualizar este {widget.type === "KPI" ? "indicador" : "contenido"}.</p>
          </div>
        )}
      </div>
      {isEditing ? <footer className="widget-footer"><span>Pos: ({widget.layout.x}, {widget.layout.y})</span><span>{widget.layout.w}×{widget.layout.h}</span></footer> : null}
    </article>
  );
}
