import type { ChartData, ChartType } from "@/types/charts";

/** Ejemplos fijos de FASE 6. No representan ventas, métricas ni consultas del usuario. */
export const CHART_DEMO_DATA: Record<ChartType, ChartData> = {
  BAR_CHART: {
    categories: ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
    series: [{ name: "Valor de ejemplo", values: [120, 180, 150, 240, 210, 300] }],
  },
  LINE_CHART: {
    categories: ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
    series: [{ name: "Valor de ejemplo", values: [80, 110, 95, 160, 190, 230] }],
  },
  PIE_CHART: {
    categories: ["Grupo A", "Grupo B", "Grupo C"],
    series: [{ name: "Valor de ejemplo", values: [45, 35, 20] }],
  },
};
