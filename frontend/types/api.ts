export type HealthResponse = { status: "ok" };
export type ApiErrorResponse = { detail: { code: string; message: string } };
export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};

export type Dashboard = {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardPage = {
  items: Dashboard[];
  total: number;
  limit: number;
  offset: number;
};

/** El backend ignora el propietario: solo el conoce el servidor. */
export type DashboardCreate = { name: string; description?: string | null };
export type DashboardUpdate = { name?: string; description?: string | null };

/** Tipos admitidos. El backend valida contra esta lista cerrada. */
export const WIDGET_TYPES = ["KPI", "BAR_CHART", "LINE_CHART", "PIE_CHART", "TABLE"] as const;
export type WidgetType = (typeof WIDGET_TYPES)[number];

/** Etiqueta en castellano para mostrar en la interfaz. */
export const WIDGET_TYPE_LABELS: Record<WidgetType, string> = {
  KPI: "Indicador (KPI)",
  BAR_CHART: "Gráfico de barras",
  LINE_CHART: "Gráfico de líneas",
  PIE_CHART: "Gráfico circular",
  TABLE: "Tabla",
};

export type Aggregation = "sum" | "avg" | "count" | "min" | "max" | "distinct_count";

/**
 * Consulta descrita de forma estructurada. El backend siempre devuelve las cuatro
 * claves, informadas o a `null`, así que se pueden leer sin comprobar antes si
 * existen.
 */
export type WidgetConfiguration = {
  dataset: string | null;
  dimension: string | null;
  metric: string | null;
  aggregation: Aggregation | null;
};

/** Posición y tamaño en las unidades de react-grid-layout. */
export type WidgetLayout = { x: number; y: number; w: number; h: number };

export type Widget = {
  id: number;
  dashboard_id: number;
  type: WidgetType;
  title: string;
  configuration: WidgetConfiguration;
  layout: WidgetLayout;
  created_at: string;
  updated_at: string;
};

export type WidgetCreate = {
  type: WidgetType;
  title?: string;
  configuration?: Partial<WidgetConfiguration>;
  layout?: WidgetLayout;
};

/** `type` y `dashboard_id` no se pueden cambiar; el backend los rechaza. */
export type WidgetUpdate = {
  title?: string;
  configuration?: Partial<WidgetConfiguration>;
  layout?: WidgetLayout;
};

export type WidgetLayoutItem = WidgetLayout & { id: number };

export type DashboardLayoutUpdate = {
  items: WidgetLayoutItem[];
};

