"use client";

import { useMemo } from "react";
import { EChart } from "@/components/charts/EChart";
import { pieOption, chartLabel } from "@/components/charts/chart-options";
import type { ChartProps } from "@/types/charts";

export function PieChart({ data, title }: ChartProps) {
  const option = useMemo(() => pieOption(data), [data]);
  return <EChart option={option} label={chartLabel(title, data)} />;
}
