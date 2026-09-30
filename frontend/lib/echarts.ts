import { init, use as registerCharts, type ComposeOption } from "echarts/core";
import { BarChart, LineChart, PieChart, type BarSeriesOption, type LineSeriesOption, type PieSeriesOption } from "echarts/charts";
import { GridComponent, TooltipComponent, LegendComponent, type GridComponentOption, type TooltipComponentOption, type LegendComponentOption } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

registerCharts([BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

export { init };
export type ChartOption = ComposeOption<
  BarSeriesOption | LineSeriesOption | PieSeriesOption |
  GridComponentOption | TooltipComponentOption | LegendComponentOption
>;

export const CHART_COLORS = ["#0f766e", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899"];
