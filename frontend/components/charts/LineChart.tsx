"use client";

import { useMemo } from "react";
import { EChart } from "@/components/charts/EChart";
import { cartesianOption, chartLabel } from "@/components/charts/chart-options";
import type { ChartProps } from "@/types/charts";

export function LineChart({ data, title }: ChartProps) {
  const option = useMemo(() => cartesianOption(data, "line"), [data]);
  return <EChart option={option} label={chartLabel(title, data)} />;
}
