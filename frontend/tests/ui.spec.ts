import { expect, test, type Page } from "@playwright/test";
import type { Widget } from "../types/api";

async function mockDashboard(page: Page, failCreation = false) {
  const date = "2026-09-30T12:00:00Z";
  let name = "Análisis comercial";
  const widgets: Widget[] = [{
    id: 1, dashboard_id: 1, type: "BAR_CHART", title: "Evolución mensual",
    configuration: { dataset: null, dimension: null, metric: null, aggregation: null },
    layout: { x: 0, y: 0, w: 6, h: 5 }, created_at: date, updated_at: date,
  }];
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    let body: unknown;
    if (path.endsWith("/auth/me")) {
      body = { id: 1, email: "demo@example.com", full_name: "Marvin Zúñiga", is_active: true, created_at: date };
    } else if (path.endsWith("/dashboards/1")) {
      if (request.method() === "PATCH") name = request.postDataJSON().name;
      body = { id: 1, name, description: "Resumen de mi negocio", created_at: date, updated_at: date };
    } else if (path.endsWith("/widgets")) {
      if (request.method() === "POST") {
        if (failCreation) {
          await route.fulfill({ status: 422, json: { detail: { code: "VALIDATION_ERROR", message: "No se pudo crear el widget." } } });
          return;
        }
        const payload = request.postDataJSON();
        const widget: Widget = { ...widgets[0], id: 2, type: payload.type, title: payload.title || "Indicador", layout: { x: 0, y: 5, w: 4, h: 3 } };
        widgets.push(widget);
        body = widget;
      } else body = widgets;
    } else throw new Error(`Petición inesperada: ${request.method()} ${path}`);
    await route.fulfill({ json: body });
  });
  await page.goto("/dashboards/1");
  await expect(page.getByRole("heading", { name: "Análisis comercial", exact: true })).toBeVisible();
}

test("separa lectura y edición; conserva el alta de widgets y el cambio de nombre", async ({ page }, testInfo) => {
  const renderErrors: string[] = [];
  page.on("console", message => { if (message.type() === "error") renderErrors.push(message.text()); });
  await mockDashboard(page);
  await expect(page.getByLabel("Nuevo nombre")).toHaveCount(0);
  await expect(page.getByLabel("Tipo", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Eliminar widget Evolución mensual" })).toHaveCount(0);
  await expect(page.locator("canvas")).toHaveCount(1);
  await page.screenshot({ path: testInfo.outputPath("dashboard-desktop.png"), fullPage: true });
  await page.getByRole("button", { name: "Añadir widget", exact: true }).click();
  await expect(page.getByRole("button", { name: "Terminar edición", exact: true })).toBeVisible();
  await page.getByLabel("Tipo", { exact: true }).selectOption("KPI");
  await page.getByLabel("Título").fill("Mi indicador");
  await page.getByRole("button", { name: "Crear widget", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mi indicador", exact: true })).toBeVisible();
  await expect(page.getByLabel("Tipo", { exact: true })).toHaveCount(0);
  await page.getByText("Propiedades del dashboard", { exact: true }).click();
  await page.getByLabel("Nuevo nombre", { exact: true }).fill("Ventas y resultados");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Ventas y resultados", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Terminar edición", exact: true }).click();
  await expect(page.getByRole("button", { name: "Eliminar widget Mi indicador", exact: true })).toHaveCount(0);
  await expect(page.getByText("Vista de lectura", { exact: true })).toBeVisible();
  expect(renderErrors).toEqual([]);
});

test("mantiene visible un error de creación en el formulario", async ({ page }) => {
  await mockDashboard(page, true);
  await page.getByRole("button", { name: "Añadir widget", exact: true }).click();
  await page.getByRole("button", { name: "Crear widget", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "No se pudo crear el widget." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Crear widget", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cerrar formulario de widget" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "No se pudo crear el widget." })).toBeVisible();
});

test("navegación móvil y lienzo sin desbordamiento horizontal", async ({ page }, testInfo) => {
  await mockDashboard(page);
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await expect(page.getByRole("button", { name: "Añadir widget", exact: true })).toBeVisible();
  }
  await page.getByRole("button", { name: "Abrir navegación" }).click();
  await expect(page.getByRole("button", { name: "Cerrar sesión", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cerrar navegación" }).click();
  await expect(page.getByRole("button", { name: "Cerrar sesión", exact: true })).toBeHidden();
  await page.screenshot({ path: testInfo.outputPath("dashboard-mobile.png"), fullPage: true });
  await page.getByRole("button", { name: "Añadir widget", exact: true }).click();
  await expect(page.getByRole("button", { name: "Crear widget", exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
