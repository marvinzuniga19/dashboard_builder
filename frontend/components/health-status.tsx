"use client";

import { useEffect, useState } from "react";
import { apiGet, apiUrl } from "@/lib/api";
import type { HealthResponse } from "@/types/api";

type Status = "loading" | "success" | "error";

export function HealthStatus() {
  const [status, setStatus] = useState<Status>("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    apiGet<HealthResponse>("/health", controller.signal)
      .then((data) => { if (active) setStatus(data.status === "ok" ? "success" : "error"); })
      .catch(() => { if (active) setStatus("error"); })
      .finally(() => window.clearTimeout(timeout));
    return () => {
      active = false;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [attempt]);

  const label = {
    loading: "Comprobando conexión…",
    success: "API y base de datos disponibles",
    error: "No se pudo conectar con la API",
  }[status];

  return (
    <section className="surface flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between" aria-label="Estado del backend">
      <div aria-live="polite">
        <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">Conexión local</p>
        <p className="flex items-center gap-3 font-semibold">
          <span className={`h-2.5 w-2.5 rounded-full ${status === "success" ? "bg-emerald-500" : status === "error" ? "bg-amber-500" : "bg-slate-400"}`} />
          {label}
        </p>
        <p className="mt-2 break-all text-sm text-slate-500">{apiUrl("/health")}</p>
        {status === "error" && <p className="mt-2 text-sm text-slate-500">Inicia el backend y verifica la URL y el origen CORS.</p>}
      </div>
      <button
        className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-700 disabled:opacity-50"
        disabled={status === "loading"}
        onClick={() => { setStatus("loading"); setAttempt((value) => value + 1); }}
      >Comprobar conexión</button>
    </section>
  );
}
