"use client";

import dynamic from "next/dynamic";
import { validateChartData, type ChartData, type ChartType } from "@/types/charts";

const loading = () => <p role="status" className="p-3 text-sm text-slate-500">Cargando gráfico…</p>;
const BarChart = dynamic(() => import("./BarChart").then((module) => module.BarChart), { ssr: false, loading });
const LineChart = dynamic(() => import("./LineChart").then((module) => module.LineChart), { ssr: false, loading });
const PieChart = dynamic(() => import("./PieChart").then((module) => module.PieChart), { ssr: false, loading });

export function ChartRenderer({ type, data, title }: { type: ChartType; data: ChartData; title: string }) {
  const error = validateChartData(data, type);
  if (error) return <p role="alert" className="p-3 text-sm text-red-700">{error}</p>;
  if (!data.categories.length || !data.series.length ||
    (type === "PIE_CHART" && data.series[0].values.every((value) => value === 0))) {
    return <p className="p-3 text-sm text-slate-500">Sin datos para mostrar.</p>;
  }
  switch (type) {
    case "BAR_CHART": return <BarChart data={data} title={title} />;
    case "LINE_CHART": return <LineChart data={data} title={title} />;
    case "PIE_CHART": return <PieChart data={data} title={title} />;
  }
}
