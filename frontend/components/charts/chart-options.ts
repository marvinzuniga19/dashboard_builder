import { CHART_COLORS, type ChartOption } from "@/lib/echarts";
import type { ChartData } from "@/types/charts";

export function cartesianOption(data: ChartData, type: "bar" | "line"): ChartOption {
  return {
    animation: false,
    color: CHART_COLORS,
    textStyle: { fontFamily: "Arial, sans-serif", color: "#64748b" },
    tooltip: { trigger: "axis", renderMode: "richText", confine: true },
    legend: { type: "scroll", top: 0, textStyle: { fontSize: 10 }, data: data.series.map((series) => series.name) },
    grid: { left: 8, right: 12, top: 35, bottom: 8, containLabel: true },
    xAxis: { type: "category", data: data.categories, axisLabel: { hideOverlap: true, fontSize: 10 }, axisTick: { show: false } },
    yAxis: { type: "value", axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { color: "#e2e8f0" } } },
    series: data.series.map((series) => ({ name: series.name, type, data: series.values })),
  };
}

export function pieOption(data: ChartData): ChartOption {
  return {
    animation: false,
    color: CHART_COLORS,
    tooltip: { trigger: "item", renderMode: "richText", confine: true },
    legend: { type: "scroll", bottom: 0, textStyle: { fontSize: 10 } },
    series: [{
      type: "pie",
      name: data.series[0].name,
      radius: ["32%", "65%"],
      center: ["50%", "43%"],
      label: { show: false },
      itemStyle: { borderColor: "#fff", borderWidth: 2 },
      data: data.categories.map((name, index) => ({ name, value: data.series[0].values[index] })),
    }],
  };
}

export function chartLabel(title: string, data: ChartData): string {
  return `${title}. ${data.series.map((series) => `${series.name}: ${data.categories.map((category, index) => `${category} ${series.values[index]}`).join(", ")}`).join(". ")}`;
}
