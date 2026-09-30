"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useLogin, useSession } from "@/hooks/useAuth";

export default function LoginPage() {
  const router = useRouter();
  const session = useSession();
  const { login, error, isSubmitting } = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (session.state === "authenticated") {
      router.replace("/");
    }
  }, [session.state, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const user = await login({ email, password });
    if (user) {
      router.replace("/");
    }
  }

  if (session.state === "loading") {
    return <AuthFrame title="Comprobando sesión…" description="Un momento." />;
  }

  if (session.state === "error") {
    return (
      <AuthFrame
        title="No se pudo contactar con la API"
        description={session.error ?? "Comprueba que el backend esté activo en el puerto 8000."}
      >
        <Link href="/login" className="text-sm font-semibold text-teal-800 underline">
          Reintentar
        </Link>
      </AuthFrame>
    );
  }

  return (
    <AuthFrame
      title="Inicia sesión"
      description="Accede a tu espacio de análisis para construir dashboards."
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <div className="space-y-2">
          <label htmlFor="email" className="block text-sm font-semibold text-slate-700">
            Correo electrónico
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="tu@empresa.com"
            aria-describedby={error ? "login-error" : undefined}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-teal-700 focus:ring-4 focus:ring-teal-100"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-semibold text-slate-700">
            Contraseña
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-describedby={error ? "login-error" : undefined}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-teal-700 focus:ring-4 focus:ring-teal-100"
          />
        </div>

        {error ? (
          <p
            id="login-error"
            role="alert"
            className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
          >
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting || email === "" || password === ""}
          className="w-full rounded-xl bg-teal-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "Comprobando…" : "Entrar"}
        </button>
      </form>

      <p className="mt-6 text-xs leading-5 text-slate-500">
        ¿Aún no tienes cuenta? Créala en local con{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5">python -m app.cli.create_user</code>.
      </p>
    </AuthFrame>
  );
}

function AuthFrame({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-800 text-lg font-bold text-white">
            D
          </span>
          <div>
            <p className="font-bold tracking-tight">Dashboard Builder</p>
            <p className="text-xs text-slate-500">Tu espacio de análisis</p>
          </div>
        </div>

        <section className="surface p-7">
          <h1 className="text-xl font-bold tracking-tight">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
          {children ? <div className="mt-6">{children}</div> : null}
        </section>
      </div>
    </main>
  );
}
