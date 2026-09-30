"use client";

/**
 * DashboardGrid — lienzo interactivo de widgets.
 *
 * Usa la API v2 de react-grid-layout con useContainerWidth + ReactGridLayout.
 * El layout persiste al soltar el drag o terminar el resize; no se envía ninguna
 * petición HTTP durante el movimiento.
 *
 * El handle de arrastre es `.widget-drag-handle`: los clics en botones del widget
 * (eliminar, etc.) no activan el drag.
 */

import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

import { useCallback, useState } from "react";
import ReactGridLayout, {
  type Layout as RGLLayout,
  useContainerWidth,
  verticalCompactor,
} from "react-grid-layout";

import { WidgetCard } from "@/components/widgets/widget-card";
import type { Widget, WidgetLayoutItem } from "@/types/api";

const GRID_COLS = 12;
const ROW_HEIGHT = 60; // px por unidad de fila

type DashboardGridProps = {
  widgets: Widget[];
  onRemoveWidget: (id: number, title: string) => void;
  onLayoutChange: (items: WidgetLayoutItem[]) => void;
  isSubmitting?: boolean;
  isEditing?: boolean;
};

/** Convierte el array de widgets de la API al formato de LayoutItem de RGL. */
function widgetsToLayout(widgets: Widget[]): RGLLayout {
  return widgets.map((w) => ({
    i: String(w.id),
    x: w.layout.x,
    y: w.layout.y,
    w: w.layout.w,
    h: w.layout.h,
    minW: 2,
    minH: 2,
  }));
}

/** Convierte el Layout de RGL de vuelta al formato del backend. */
function layoutToItems(layout: RGLLayout): WidgetLayoutItem[] {
  return layout.map((item) => ({
    id: Number(item.i),
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
  }));
}

/** Comprueba si dos layouts son equivalentes para evitar peticiones innecesarias. */
function layoutsEqual(a: RGLLayout, b: RGLLayout): boolean {
  if (a.length !== b.length) return false;
  const mapB = new Map(b.map((item) => [item.i, item]));
  return a.every((itemA) => {
    const itemB = mapB.get(itemA.i);
    return (
      itemB !== undefined &&
      itemA.x === itemB.x &&
      itemA.y === itemB.y &&
      itemA.w === itemB.w &&
      itemA.h === itemB.h
    );
  });
}

export function DashboardGrid({
  widgets,
  onRemoveWidget,
  onLayoutChange,
  isSubmitting = false,
  isEditing = false,
}: DashboardGridProps) {
  const { width, containerRef, mounted } = useContainerWidth({ initialWidth: 1200 });

  // Layout local que se actualiza durante drag/resize pero solo persiste al soltar.
  const [localLayout, setLocalLayout] = useState<RGLLayout>(() => widgetsToLayout(widgets));

  // Reinicia antes de renderizar RGL cuando cambia el conjunto de widgets.
  // Evita que el layout anterior y los nuevos hijos compitan durante un alta/baja.
  const ids = widgets.map((widget) => widget.id).sort((a, b) => a - b).join(",");
  const [widgetIds, setWidgetIds] = useState(ids);
  if (ids !== widgetIds) {
    setWidgetIds(ids);
    setLocalLayout(widgetsToLayout(widgets));
  }

  /** Durante drag/resize solo actualizamos estado local (sin HTTP). */
  const handleLayoutChange = useCallback((newLayout: RGLLayout) => {
    setLocalLayout((current) => layoutsEqual(current, newLayout) ? current : newLayout);
  }, []);

  /** Persiste el layout final que entrega RGL, sin efectos dentro de un updater de React. */
  const handleInteractionStop = useCallback((newLayout: RGLLayout) => {
    if (!isEditing) return;
    setLocalLayout((current) => layoutsEqual(current, newLayout) ? current : newLayout);
    if (!layoutsEqual(newLayout, widgetsToLayout(widgets))) {
      onLayoutChange(layoutToItems(newLayout));
    }
  }, [widgets, onLayoutChange, isEditing]);

  if (widgets.length === 0) {
    return null; // El padre muestra el estado vacío.
  }

  // Antes de la primera medición renderizamos el contenedor vacío para evitar
  // un layout calculado con ancho incorrecto.
  return (
    <div ref={containerRef} className="w-full">
      {mounted && (
        <ReactGridLayout
          layout={localLayout}
          width={width}
          gridConfig={{ cols: GRID_COLS, rowHeight: ROW_HEIGHT, margin: [12, 12] }}
          dragConfig={{ enabled: isEditing && !isSubmitting, handle: ".widget-drag-handle" }}
          resizeConfig={{ enabled: isEditing && !isSubmitting, handles: ["se", "s", "e"] }}
          compactor={verticalCompactor}
          autoSize
          onLayoutChange={handleLayoutChange}
          onDragStop={handleInteractionStop}
          onResizeStop={handleInteractionStop}
          className={`dashboard-grid ${isEditing ? "is-editing" : "is-reading"}`}
        >
          {widgets.map((widget) => (
            <div key={String(widget.id)} className="overflow-hidden rounded-[10px]">
              <WidgetCard
                widget={widget}
                onRemove={onRemoveWidget}
                isRemoving={isSubmitting}
                isEditing={isEditing}
              />
            </div>
          ))}
        </ReactGridLayout>
      )}
    </div>
  );
}
