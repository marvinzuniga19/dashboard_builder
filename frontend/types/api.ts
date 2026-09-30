export type HealthResponse = { status: "ok" };
export type ApiErrorResponse = { detail: { code: string; message: string } };
export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};
