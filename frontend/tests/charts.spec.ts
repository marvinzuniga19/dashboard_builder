import { expect, test } from "@playwright/test";
import { validateChartData } from "../types/charts";
import type { Widget, WidgetLayoutItem } from "../types/api";

test("rechaza series desalineadas, valores no finitos y sectores negativos", () => {
  expect(validateChartData({ categories: ["A"], series: [{ name: "Valor", values: [] }] }, "BAR_CHART")).not.toBeNull();
  expect(validateChartData({ categories: ["A"], series: [{ name: "Valor", values: [NaN] }] }, "LINE_CHART")).not.toBeNull();
  expect(validateChartData({ categories: ["A"], series: [{ name: "Valor", values: [-1] }] }, "PIE_CHART")).not.toBeNull();
  expect(validateChartData({ categories: ["A"], series: [{ name: "Valor", values: [0] }] }, "BAR_CHART")).toBeNull();
});

test("renderiza los tres gráficos, adapta el canvas y conserva el layout devuelto por la API", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const date = "2026-09-30T12:00:00Z";
  let widgets: Widget[] = ["BAR_CHART", "LINE_CHART", "PIE_CHART"].map((type, index) => ({
    id: index + 1, dashboard_id: 1, type: type as Widget["type"], title: `Ejemplo ${index + 1}`,
    configuration: { dataset: null, dimension: null, metric: null, aggregation: null },
    layout: { x: 0, y: index * 5, w: 6, h: 5 }, created_at: date, updated_at: date,
  }));
  let savedLayouts = 0;
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    let body: unknown;
    if (path.endsWith("/auth/me")) {
      body = { id: 1, email: "demo@example.com", full_name: "Demo", is_active: true, created_at: date };
    } else if (path.endsWith("/dashboards/1")) {
      body = { id: 1, name: "Prueba de gráficos", description: null, created_at: date, updated_at: date };
    } else if (path.endsWith("/layouts")) {
      const items = request.postDataJSON().items as WidgetLayoutItem[];
      widgets = widgets.map((widget) => {
        const layout = items.find((item) => item.id === widget.id);
        return layout ? { ...widget, layout: { x: layout.x, y: layout.y, w: layout.w, h: layout.h } } : widget;
      });
      savedLayouts++;
      body = widgets;
    } else if (request.method() === "DELETE") {
      widgets = widgets.filter((widget) => !path.endsWith(`/widgets/${widget.id}`));
      await route.fulfill({ status: 204 });
      return;
    } else if (path.endsWith("/widgets")) {
      body = widgets;
    } else {
      throw new Error(`Petición inesperada: ${request.method()} ${path}`);
    }
    await route.fulfill({ json: body });
  });

  await page.goto("/dashboards/1");
  await expect(page.locator("canvas")).toHaveCount(3);
  await expect(page.getByText("Datos de demostración · Sin fuente conectada")).toHaveCount(3);
  // Detecta canvases vacíos, no solo la presencia del nodo.
  await expect.poll(() => page.locator("canvas").evaluateAll((canvases) => canvases.every((node) => {
    const canvas = node as HTMLCanvasElement;
    const context = canvas.getContext("2d");
    return canvas.width > 0 && canvas.height > 0 && context !== null &&
      context.getImageData(0, 0, canvas.width, canvas.height).data.some((value) => value !== 0);
  }))).toBe(true);

  const card = page.locator(".react-grid-item").filter({ has: page.getByRole("heading", { name: "Ejemplo 1", exact: true }) });
  const chart = card.getByRole("img");
  const before = await chart.boundingBox();
  expect(before).not.toBeNull();
  await expect(card.getByRole("button", { name: "Arrastrar para mover widget" })).toHaveCount(0);
  await expect(card.locator(".react-resizable-handle-se")).toBeHidden();
  await page.getByRole("button", { name: "Editar", exact: true }).click();
  const handle = card.locator(".react-resizable-handle-se");
  await handle.scrollIntoViewIfNeeded();
  const bounds = await handle.boundingBox();
  if (!bounds) throw new Error("No se encontró el control de redimensionado");
  await page.mouse.move(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
  await page.mouse.down();
  await page.mouse.move(bounds.x + bounds.width / 2 + 100, bounds.y + bounds.height / 2 + 72, { steps: 12 });
  await page.mouse.up();
  await expect.poll(() => savedLayouts).toBe(1);
  await expect.poll(async () => (await chart.boundingBox())?.width ?? 0).toBeGreaterThan(before!.width);
  await expect.poll(async () => {
    const canvasWidth = (await card.locator("canvas").boundingBox())?.width ?? 0;
    const chartWidth = (await chart.boundingBox())?.width ?? 0;
    return Math.abs(canvasWidth - chartWidth);
  }).toBeLessThan(2);
  // El handle de arrastre sigue funcionando sobre los gráficos, sin guardar durante el movimiento.
  const dragHandle = card.getByRole("button", { name: "Arrastrar para mover widget" });
  await expect(dragHandle).toBeEnabled();
  await dragHandle.scrollIntoViewIfNeeded();
  const dragBounds = await dragHandle.boundingBox();
  if (!dragBounds) throw new Error("No se encontró el control de arrastre");
  await page.mouse.move(dragBounds.x + 8, dragBounds.y + 8);
  await page.mouse.down();
  await page.mouse.move(dragBounds.x + 160, dragBounds.y + 8, { steps: 12 });
  expect(savedLayouts).toBe(1);
  await page.mouse.up();
  await expect.poll(() => savedLayouts).toBe(2);
  const savedLayout = { ...widgets[0].layout };
  await page.reload();
  await expect(page.locator("canvas")).toHaveCount(3);
  await expect(page.getByText("Vista de lectura", { exact: true })).toBeVisible();
  await expect(card.getByRole("button", { name: "Eliminar widget Ejemplo 1", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Editar", exact: true }).click();
  await expect(card.getByText(`${savedLayout.w}×${savedLayout.h}`)).toBeVisible();

  await page.setViewportSize({ width: 780, height: 900 });
  await expect.poll(async () => (await chart.boundingBox())?.width ?? 0).toBeLessThan(before!.width);
  page.on("dialog", (dialog) => dialog.accept());
  await card.getByRole("button", { name: "Eliminar widget Ejemplo 1", exact: true }).click();
  await expect(page.locator("canvas")).toHaveCount(2);
  await page.reload();
  await expect(page.locator("canvas")).toHaveCount(2);
  expect(errors).toEqual([]);
});
