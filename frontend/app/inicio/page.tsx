"use client";

import { AppShell } from "@/components/app-shell";
import { HomeView } from "@/components/home-view";
import { RequireAuth } from "@/components/require-auth";

export default function InicioPage() {
  return (
    <RequireAuth>
      <AppShell>
        <HomeView />
      </AppShell>
    </RequireAuth>
  );
}
