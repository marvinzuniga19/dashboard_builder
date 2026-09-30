"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useSession } from "@/hooks/useAuth";

/**
 * Puerta de las páginas que exigen sesión.
 *
 * Los hijos se montan únicamente cuando la sesión es válida: así sus hooks de
 * SWR no disparan peticiones para un usuario que aún no ha iniciado sesión, y
 * tampoco para uno que ya no la tiene.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const session = useSession();

  useEffect(() => {
    if (session.state === "unauthenticated") {
      router.replace("/login");
    }
  }, [session.state, router]);

  if (session.state === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Comprobando sesión…
      </main>
    );
  }

  if (session.state === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center px-6 text-center">
        <div>
          <h1 className="text-lg font-bold">No se pudo contactar con la API</h1>
          <p className="mt-2 text-sm text-slate-500">
            {session.error ?? "Comprueba que el backend esté activo en el puerto 8000."}
          </p>
          <Link
            href="/login"
            className="mt-5 inline-block rounded-xl bg-teal-800 px-4 py-2.5 text-sm font-semibold text-white"
          >
            Ir al acceso
          </Link>
        </div>
      </main>
    );
  }

  if (session.user === null) {
    return null;
  }

  return <>{children}</>;
}
