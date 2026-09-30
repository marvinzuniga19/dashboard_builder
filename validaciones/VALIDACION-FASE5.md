# Validación — FASE 5

## Resultado

Grid interactivo completo de extremo a extremo: `react-grid-layout` v2 integrado con la API v2 (hooks `useContainerWidth` + `ReactGridLayout`), handle de arrastre exclusivo (`.widget-drag-handle`) para no interferir con los botones de los widgets, persistencia al soltar (drag y resize), endpoint `PUT /api/v1/dashboards/{id}/layouts` con validación de aislamiento y cobertura de pruebas.

## Entorno de validación

- Python 3.14.7, Node.js 26.10.0, SQLite 3.53.4.
- FastAPI 0.142.1, SQLAlchemy 2.0.54, Pydantic 2.13.5, Alembic 1.20.0, Next.js 16.3.7, React 19.3.
- Nueva dependencia: `react-grid-layout@2.2.4` (solo frontend, sin cambios en `requirements.txt`).

## Verificaciones ejecutadas

### Backend

- `python -m pytest -q`: **174 pruebas aprobadas** (162 de las fases anteriores y **12 nuevas** de la FASE 5), con la misma advertencia de deprecación del adaptador TestClient/httpx de Starlette.
- `alembic check`: **no hay operaciones de actualización pendientes** — la FASE 5 no introduce cambios de esquema.
- CORS actualizado: `PUT` añadido a `allow_methods`; no rompe los endpoints existentes.

Pruebas nuevas del endpoint `PUT /api/v1/dashboards/{id}/layouts`:

| Caso | Resultado |
| --- | --- |
| Lote con 2 widgets, posiciones distintas | 200, layout devuelto correcto; `GET /widgets` posterior confirma persistencia |
| Lote vacío con 1 widget existente | 200, el widget no se mueve; lista devuelta correcta |
| Id duplicado en el lote | 422 `VALIDATION_ERROR` |
| `x` negativo | 422 |
| `y` negativo | 422 |
| `w` = 0 | 422 |
| `w` = 13 (> 12 columnas) | 422 |
| `h` = 0 | 422 |
| `h` = 25 (> máximo) | 422 |
| Widget ajeno en el lote de `other_user` | 404 `WIDGET_NOT_FOUND` |
| Dashboard ajeno | 404 `WIDGET_NOT_FOUND` |
| Sin cookie de sesión | 401 `AUTH_REQUIRED` |

### Frontend

- `npm run typecheck`: aprobado sin errores.
- `npm run lint`: aprobado sin advertencias.
- `npm run build`: aprobado; rutas `/`, `/_not-found`, `/dashboards`, `/dashboards/[id]` (dinámica), `/inicio` y `/login`.
- `next-env.d.ts` revertido tras el build (mismo comportamiento que en FASES 3 y 4).

## Incidencias encontradas y corregidas durante la fase

1. **Las dependencias de los callbacks `onDragStop`/`onResizeStop` declaraban parámetros `_layout`, `_old`, `_new` que el linter marcaba como "defined but never used".** Simplificado a `() => { … }` sin parámetros; la información que se necesita ya viene de la referencia a `widgets` en el closure.

2. **`PUT` no estaba en `allow_methods` del CORS del backend.** El comentario original de `api.ts` incluso advertía de ello. Se añadió `PUT` a la lista y se eliminó el comentario obsoleto; sin ese cambio el preflight CORS habría bloqueado la petición desde el navegador.

3. **Las pruebas iniciales referenciaban fixtures `auth_client`, `second_auth_client` y `second_dashboard` que no existen.** Se adaptaron a los fixtures reales del proyecto (`logged_in_client`, `other_user_client`, `dashboard`) con acceso al `.id` directamente.

4. **El test de ids duplicados comprobaba la cadena `"duplicado"` en la respuesta**, pero el manejador global de errores de validación devuelve `VALIDATION_ERROR` con mensaje genérico. Se ajustó la aserción a verificar el código.

5. **`ReactGridLayout` (v2) exige la prop `width` en píxeles** (rompe con `WidthProvider` de v1). Se usa `useContainerWidth` con el ref sobre el contenedor y el guard `mounted` para evitar hidratación incorrecta en SSR.

## Decisiones tomadas durante la fase

- **Handle de arrastre explícito** (`.widget-drag-handle`): evita que un clic en el botón «Eliminar» del widget dispare el drag. El grip con seis puntos es visualmente claro y no consume espacio significativo.
- **Actualización optimista de SWR**: `updateLayouts` muta la caché local antes de la petición HTTP, eliminando el salto visual al soltar un widget.
- **Endpoint dual `PUT` + `PATCH`** para el mismo handler: el frontend usa `PUT` (semántica de reemplazar el layout completo); `PATCH` queda como alias por si en el futuro se necesita una actualización parcial desde otra ruta.
- **Comparación de layouts antes de persistir**: si el usuario arrastra y devuelve el widget exactamente al mismo sitio, `layoutsEqual` devuelve `true` y no se lanza ninguna petición HTTP.
- **`react-grid-layout` v2** en lugar de `v1/legacy`: el proyecto es nuevo, sin deuda de migración, y la API de hooks es más composable y compatible con React 19 sin necesidad de HOC (`WidthProvider`).
- **Sin migración de esquema**: las coordenadas ya estaban en columnas individuales (`x`, `y`, `w`, `h`) desde la FASE 4; el endpoint nuevo solo las lee y escribe en lote.
- **`minW: 2`, `minH: 2` en el grid**: evita que un resize accidental deje un widget inutilizable de 1 celda.

## Límites de la validación

- **No se verificó el flujo en un navegador.** El entorno no tiene Chromium ni Playwright. Se comprobaron las respuestas HTTP y que las rutas sirven con `npm run build`, pero no la experiencia interactiva de drag & drop.
- Sin compresión de layout en base de datos: se guardan todas las posiciones en cada `PUT`, lo que es adecuado para el número actual de widgets por dashboard.
- No existe paginación ni límite de widgets por dashboard; el `PUT /layouts` devuelve el conjunto completo, que es lo que necesita el grid para reconstruir el estado.

## Migraciones

No se añadió ninguna migración: el esquema ya contenía las columnas `x`, `y`, `w`, `h` desde `0004_widgets`.

## Archivos principales modificados o creados

### Backend

| Archivo | Cambio |
| --- | --- |
| `app/schemas/widget.py` | Nuevos schemas `WidgetLayoutItem` y `DashboardLayoutUpdate` |
| `app/services/widget_service.py` | Nueva función `update_dashboard_layouts` |
| `app/api/routes/widgets.py` | Nuevo endpoint `PUT` (+ alias `PATCH`) `/dashboards/{id}/layouts` |
| `app/main.py` | `PUT` añadido a `allow_methods` del CORS |
| `tests/test_widgets.py` | 12 nuevas pruebas de la FASE 5 |

### Frontend

| Archivo | Cambio |
| --- | --- |
| `package.json` / `node_modules` | `react-grid-layout@2.2.4` instalado |
| `types/api.ts` | Nuevos tipos `WidgetLayoutItem` y `DashboardLayoutUpdate` |
| `lib/api.ts` | `PUT` añadido a `RequestOptions`; exportada `apiPut` |
| `hooks/useWidgets.ts` | `updateLayouts` en `WidgetActions`; `useWidgetActions` implementado |
| `components/dashboard/dashboard-grid.tsx` | Nuevo componente con RGL v2 |
| `components/widgets/widget-card.tsx` | Nueva tarjeta de widget con grip handle |
| `app/dashboards/[id]/page.tsx` | Integra `DashboardGrid`; elimina la lista estática de tarjetas |
| `app/globals.css` | Estilos para el grid, placeholder, resize handle y grab cursor |

## Siguientes fases pendientes

Fases 5 a 10 del roadmap en AGENTS.md: ECharts, fuentes de datos, query engine y widget builder. La FASE 6 (ECharts) puede comenzar inmediatamente: el `WidgetCard` ya distingue `KPI` del resto y tiene el espacio reservado para el gráfico.

## Commit sugerido

```bash
git commit -m "feat(grid): react-grid-layout drag & drop, resize y persistencia de layout — FASE 5"
```
