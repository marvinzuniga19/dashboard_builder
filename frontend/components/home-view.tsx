import { HealthStatus } from "@/components/health-status";

const nextSteps = [
  { number: "04", title: "Widgets", description: "Indicadores, gráficos y tablas configurables." },
  { number: "05", title: "Dashboard Grid", description: "Arrastrar, redimensionar y guardar layouts." },
  { number: "06", title: "ECharts", description: "Gráficos con la librería ligera de ECharts." },
];

const stack = [
  { title: "Frontend", value: "Next.js", detail: "App Router · TypeScript · Tailwind · SWR" },
  { title: "Backend", value: "FastAPI", detail: "API v1 · Pydantic v2 · Python" },
  { title: "Persistencia", value: "SQLite", detail: "SQLAlchemy async · Alembic" },
];

/**
 * Contenido de `/inicio`. El shell, la navegación y la sesión los aporta
 * `AppShell`, así que aquí no se reciben como props.
 */
export function HomeView() {
  return (
    <main className="mx-auto max-w-6xl space-y-7 px-6 py-10 lg:px-10 lg:py-12">
      <section>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-700">
          Sesión protegida
        </p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
          Dashboard Builder
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-500">
          Esta pantalla solo es visible con una sesión válida. El token viaja en una cookie
          httpOnly y nunca se guarda en el navegador.
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
          Tercera etapa completada
        </p>
        <h2 className="mt-3 text-xl font-bold">Dashboards: listados, altas y edición</h2>
        <ul className="mt-4 space-y-2 text-sm leading-7 text-slate-500">
          <li>· Cada dashboard pertenece a su usuario y no se comparte sin permiso.</li>
          <li>· Listado paginado, ordenado por última modificación.</li>
          <li>· Un dashboard ajeno responde como si no existiera.</li>
          <li>· Sesión por cookie httpOnly y contraseñas con bcrypt.</li>
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
        Dashboard Builder · v0.3.0 · Dashboards
      </footer>
    </main>
  );
}
