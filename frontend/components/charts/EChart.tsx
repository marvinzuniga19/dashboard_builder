"use client";

import { useEffect, useRef, useState } from "react";
import type { EChartsType } from "echarts/core";

import { init, type ChartOption } from "@/lib/echarts";

/** Una instancia por contenedor, también bajo React Strict Mode. */
export function EChart({ option, label }: { option: ChartOption; label: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<EChartsType | null>(null);
  const optionRef = useRef(option);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    optionRef.current = option;
    chartRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let frame = 0;

    const render = () => {
      if (!container.clientWidth || !container.clientHeight) return;
      try {
        if (!chartRef.current) {
          chartRef.current = init(container, undefined, { renderer: "canvas" });
          chartRef.current.setOption(optionRef.current, { notMerge: true });
        } else {
          chartRef.current.resize();
        }
      } catch {
        chartRef.current?.dispose();
        chartRef.current = null;
        setFailed(true);
      }
    };

    const scheduleRender = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(render);
    };
    const observer = new ResizeObserver(scheduleRender);
    observer.observe(container);
    scheduleRender();

    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  return (
    <div className="relative h-full min-h-[140px] w-full min-w-0">
      <div ref={containerRef} role="img" aria-label={label} className="h-full min-h-[140px] w-full" />
      {failed ? (
        <p role="alert" className="absolute inset-0 flex items-center justify-center bg-white p-3 text-center text-sm text-red-700">
          No se pudo mostrar el gráfico. Recarga la página para reintentar.
        </p>
      ) : null}
    </div>
  );
}
