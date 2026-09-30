"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Activity, ChevronRight, Database, LayoutDashboard, LogOut, Menu, X } from "lucide-react";

import { useLogout, useSession } from "@/hooks/useAuth";

const NAVIGATION = [
  { href: "/dashboards", label: "Dashboards", icon: LayoutDashboard },
  { href: "/inicio", label: "Estado del sistema", icon: Activity },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const session = useSession();
  const { logout, isSubmitting } = useLogout();
  const [mobileOpen, setMobileOpen] = useState(false);
  if (!session.user) return null;

  const displayName = session.user.full_name?.trim() || session.user.email;
  const initials = displayName.split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div className="app-layout">
      <aside className={`app-sidebar ${mobileOpen ? "is-open" : ""}`} id="app-navigation">
        <Link href="/dashboards" className="app-brand" onClick={() => setMobileOpen(false)}>
          <span className="brand-mark">DB</span>
          <span>Dashboard<span className="block font-normal text-slate-400">Builder</span></span>
        </Link>
        <div className="sidebar-navigation">
          <p className="sidebar-label">Espacio de trabajo</p>
          <nav aria-label="Navegación principal">
            {NAVIGATION.map(({ href, label, icon: Icon }) => {
              const current = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link key={href} href={href} aria-current={current ? "page" : undefined}
                  className={`sidebar-link ${current ? "is-active" : ""}`} onClick={() => setMobileOpen(false)}>
                  <Icon size={18} aria-hidden="true" />{label}
                </Link>
              );
            })}
            <span className="sidebar-link sidebar-future" aria-label="Fuentes de datos, próximamente">
              <Database size={18} aria-hidden="true" /><span>Fuentes de datos<span className="block text-[11px] text-slate-400">Próximamente</span></span>
            </span>
          </nav>
        </div>
        <div className="sidebar-account">
          <div className="flex min-w-0 items-center gap-3">
            <span className="account-avatar" aria-hidden="true">{initials}</span>
            <div className="min-w-0"><p className="truncate text-sm font-medium" title={displayName}>{displayName}</p>
              <p className="truncate text-xs text-slate-400" title={session.user.email}>{session.user.email}</p></div>
          </div>
          <button type="button" onClick={logout} disabled={isSubmitting} className="sidebar-logout">
            <LogOut size={15} aria-hidden="true" />{isSubmitting ? "Cerrando sesión…" : "Cerrar sesión"}
          </button>
        </div>
      </aside>
      <div className="app-workspace">
        <header className="app-topbar">
          <div className="flex min-w-0 items-center gap-3">
            <button type="button" className="ui-button ui-icon-button mobile-menu" aria-label={mobileOpen ? "Cerrar navegación" : "Abrir navegación"}
              aria-expanded={mobileOpen} aria-controls="app-navigation" onClick={() => setMobileOpen((open) => !open)}>
              {mobileOpen ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
            </button>
            <nav aria-label="Ruta de navegación" className="breadcrumb">
              <Link href="/dashboards">Espacio personal</Link><ChevronRight size={14} aria-hidden="true" />
              <span aria-current="page">{titleFor(pathname)}</span>
            </nav>
          </div>
          <span className="workspace-label">Personal</span>
        </header>
        {children}
      </div>
    </div>
  );
}

function titleFor(pathname: string): string {
  if (pathname === "/inicio") return "Estado del sistema";
  if (pathname === "/dashboards" || pathname === "/") return "Dashboards";
  return "Detalle del dashboard";
}
