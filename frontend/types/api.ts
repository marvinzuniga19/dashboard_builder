export type HealthResponse = { status: "ok" };
export type ApiErrorResponse = { detail: { code: string; message: string } };
export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};

export type Dashboard = {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardPage = {
  items: Dashboard[];
  total: number;
  limit: number;
  offset: number;
};

/** El backend ignora el propietario: solo el conoce el servidor. */
export type DashboardCreate = { name: string; description?: string | null };
export type DashboardUpdate = { name?: string; description?: string | null };
