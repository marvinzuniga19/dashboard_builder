"use client";

import { ShieldCheck } from "lucide-react";
import { HealthStatus } from "@/components/health-status";
import { useSession } from "@/hooks/useAuth";

export function HomeView() {
  const { user } = useSession();
  return (
    <main className="ui-page max-w-5xl space-y-7">
      <section><p className="ui-eyebrow">Tu espacio de trabajo</p><h1 className="ui-heading">Estado del sistema</h1>
        <p className="ui-subtitle">Comprueba la conexión del servicio y la cuenta con la que estás trabajando.</p></section>
      <HealthStatus />
      <section className="surface flex items-start gap-4 p-6">
        <span className="rounded-lg bg-teal-50 p-2 text-teal-800"><ShieldCheck size={20} aria-hidden="true" /></span>
        <div className="min-w-0"><h2 className="text-sm font-semibold">Sesión activa</h2>
          <p className="mt-2 break-words text-sm text-slate-600">{user?.full_name || user?.email}</p>
          {user?.full_name ? <p className="mt-1 break-words text-xs text-slate-500">{user.email}</p> : null}
          <p className="mt-3 text-xs text-slate-500">Tus dashboards y widgets están asociados a esta cuenta.</p>
        </div>
      </section>
    </main>
  );
}
