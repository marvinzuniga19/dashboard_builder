"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useLogout, useSession } from "@/hooks/useAuth";

const NAVIGATION = [
  { href: "/dashboards", label: "Dashboards" },
  { href: "/inicio", label: "Inicio del proyecto" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const session = useSession();
  const { logout, isSubmitting } = useLogout();

  // `useSession` garantiza una sesión válida antes de llegar aquí, así que el
  // usuario solo puede ser null durante una revalidación en segundo plano.
  if (!session.user) {
    return null;
  }

  const displayName = session.user.full_name?.trim() || session.user.email;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-6 py-7 lg:border-r lg:border-b-0">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-800 text-lg font-bold text-white">
            D
          </span>
          <div>
            <p className="font-bold tracking-tight">Dashboard Builder</p>
            <p className="text-xs text-slate-500">Tu espacio de análisis</p>
          </div>
        </div>

        <nav className="mt-9" aria-label="Navegación principal">
          {NAVIGATION.map((item) => {
            // El detalle (`/dashboards/1`) pertenece a la sección que lo contiene,
            // así que se compara por prefijo y no solo por igualdad exacta.
            const current = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={current ? "page" : undefined}
                className={
                  current
                    ? "mb-2 block rounded-xl bg-teal-50 px-4 py-3 text-sm font-semibold text-teal-900"
                    : "mb-2 block rounded-xl px-4 py-3 text-sm text-slate-600 hover:bg-slate-50"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-10 rounded-xl border border-slate-200 p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
            Sesión activa
          </p>
          <p className="mt-2 truncate text-sm font-semibold" title={session.user.email}>
            {displayName}
          </p>
          <p className="mt-1 truncate text-xs text-slate-500" title={session.user.email}>
            {session.user.email}
          </p>
          <button
            type="button"
            onClick={logout}
            disabled={isSubmitting}
            className="mt-4 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800 disabled:opacity-50"
          >
            {isSubmitting ? "Cerrando sesión…" : "Cerrar sesión"}
          </button>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5 lg:px-10">
          <p className="text-sm text-slate-500">
            Workspace <span className="mx-2 text-slate-300">/</span>{" "}
            <span className="font-medium text-slate-800">{titleFor(pathname)}</span>
          </p>
          <span className="rounded-full bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-800">
            FASE 6
          </span>
        </header>

        {children}
      </div>
    </div>
  );
}

/** El topbar nombra la pantalla; los ids de detalle muestran su contexto. */
function titleFor(pathname: string): string {
  if (pathname === "/inicio") return "Inicio";
  if (pathname === "/dashboards" || pathname === "/") return "Dashboards";
  return "Detalle";
}
