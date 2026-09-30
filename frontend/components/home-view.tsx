import { HealthStatus } from "@/components/health-status";
import type { User } from "@/types/api";

const nextSteps = [
  { number: "03", title: "Dashboards", description: "Creación y administración de paneles." },
  { number: "04", title: "Widgets", description: "Indicadores, gráficos y tablas configurables." },
  { number: "05", title: "Dashboard Grid", description: "Arrastrar, redimensionar y guardar layouts." },
];

const stack = [
  { title: "Frontend", value: "Next.js", detail: "App Router · TypeScript · Tailwind · SWR" },
  { title: "Backend", value: "FastAPI", detail: "API v1 · Pydantic v2 · Python" },
  { title: "Persistencia", value: "SQLite", detail: "SQLAlchemy async · Alembic" },
];

export function HomeView({
  user,
  onLogout,
  isLoggingOut,
}: {
  user: User;
  onLogout: () => void;
  isLoggingOut: boolean;
}) {
  const displayName = user.full_name?.trim() || user.email;

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
          <a
            href="#inicio"
            aria-current="page"
            className="block rounded-xl bg-teal-50 px-4 py-3 text-sm font-semibold text-teal-900"
          >
            Inicio del proyecto
          </a>
          <a
            href="#proximas-fases"
            className="mt-2 block rounded-xl px-4 py-3 text-sm text-slate-600 hover:bg-slate-50"
          >
            Próximas fases
          </a>
        </nav>

        <div className="mt-10 rounded-xl border border-slate-200 p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
            Sesión activa
          </p>
          <p className="mt-2 truncate text-sm font-semibold" title={user.email}>
            {displayName}
          </p>
          <p className="mt-1 truncate text-xs text-slate-500" title={user.email}>
            {user.email}
          </p>
          <button
            type="button"
            onClick={onLogout}
            disabled={isLoggingOut}
            className="mt-4 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800 disabled:opacity-50"
          >
            {isLoggingOut ? "Cerrando sesión…" : "Cerrar sesión"}
          </button>
        </div>
      </aside>

      <div>
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5 lg:px-10">
          <p className="text-sm text-slate-500">
            Workspace <span className="mx-2 text-slate-300">/</span>{" "}
            <span className="font-medium text-slate-800">Inicio</span>
          </p>
          <span className="rounded-full bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-800">
            FASE 2
          </span>
        </header>

        <main
          id="inicio"
          className="mx-auto max-w-6xl space-y-7 px-6 py-10 lg:px-10 lg:py-12"
        >
          <section>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-700">
              Sesión protegida
            </p>
            <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Bienvenido, {user.full_name?.split(" ")[0] ?? user.email}.
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-500">
              Esta pantalla ya solo es visible con una sesión válida. El token viaja en una
              cookie httpOnly y nunca se guarda en el navegador.
            </p>
          </section>

          <HealthStatus />

          <section className="grid gap-4 sm:grid-cols-3" aria-label="Arquitectura del proyecto">
            {stack.map((item) => (
              <article key={item.title} className="surface p-6">
                <p className="text-sm text-slate-500">{item.title}</p>
                <h2 className="mt-3 text-xl font-bold">{item.value}</h2>
                <p className="mt-2 text-xs leading-5 text-slate-500">{item.detail}</p>
              </article>
            ))}
          </section>

          <section className="surface p-7">
            <p className="text-xs font-semibold uppercase tracking-widest text-teal-700">
              Segunda etapa completada
            </p>
            <h2 className="mt-3 text-xl font-bold">Acceso, sesión y usuarios locales</h2>
            <ul className="mt-4 space-y-2 text-sm leading-7 text-slate-500">
              <li>· Inicio de sesión con correo y contraseña contra el backend.</li>
              <li>· Cookie de sesión httpOnly, SameSite y con caducidad configurable.</li>
              <li>· Contraseñas almacenadas con bcrypt, nunca en texto plano.</li>
              <li>· Alta de usuarios mediante comando local, sin registro público.</li>
            </ul>
          </section>

          <section id="proximas-fases">
            <h2 className="mb-4 text-lg font-bold">Qué sigue</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              {nextSteps.map((step) => (
                <article className="surface p-5" key={step.number}>
                  <span className="text-xs font-bold text-teal-700">FASE {step.number}</span>
                  <h3 className="mt-3 font-semibold">{step.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">{step.description}</p>
                  <p className="mt-4 text-xs text-slate-400">Pendiente de implementación</p>
                </article>
              ))}
            </div>
          </section>

          <footer className="text-xs text-slate-400">
            Dashboard Builder · v0.2.0 · Autenticación local
          </footer>
        </main>
      </div>
    </div>
  );
}
