import type { WidgetType } from "@/types/api";

export type ChartType = Extract<WidgetType, "BAR_CHART" | "LINE_CHART" | "PIE_CHART">;

/** Datos ya agregados para visualizar; no contiene consultas ni opciones arbitrarias. */
export type ChartData = {
  categories: string[];
  series: { name: string; values: number[] }[];
};

export type ChartProps = { data: ChartData; title: string };

export function isChartType(type: WidgetType): type is ChartType {
  return type === "BAR_CHART" || type === "LINE_CHART" || type === "PIE_CHART";
}

export function validateChartData(data: ChartData, type: ChartType): string | null {
  if (data.categories.length === 0 || data.series.length === 0) return null;
  if (type === "PIE_CHART" && data.series.length !== 1) {
    return "El gráfico circular requiere una sola serie.";
  }
  for (const series of data.series) {
    if (series.values.length !== data.categories.length || !series.values.every(Number.isFinite)) {
      return "Las categorías y los valores del gráfico no coinciden o contienen valores no válidos.";
    }
    if (type === "PIE_CHART" && series.values.some((value) => value < 0)) {
      return "El gráfico circular requiere valores no negativos.";
    }
  }
  return null;
}
