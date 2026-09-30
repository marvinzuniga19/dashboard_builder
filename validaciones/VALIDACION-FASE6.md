# Validación — FASE 6: ECharts

## Resultado

FASE 6 implementada: gráficos de barras, líneas y circular dentro del grid mediante `ChartRenderer`. Los ejemplos están identificados en cada tarjeta como **Datos de demostración · Sin fuente conectada**. No representan métricas del usuario ni usan la configuración guardada como una consulta.

## Implementación

- Dependencia de ejecución: `echarts@6.1.0`; dependencia de desarrollo: `@playwright/test@1.63.0`, con versiones resueltas en `package-lock.json`.
- Importación modular desde `echarts/core`, `echarts/charts`, `echarts/components` y `echarts/renderers`; se registran solo barras, líneas, circular, grid, tooltip, leyenda y canvas.
- Carga diferida de los componentes con `next/dynamic` y `ssr: false`.
- `ChartData` recibe categorías y series numéricas preparadas para visualización. Se comprueban longitudes, valores finitos y valores no negativos para el circular; este último exige una sola serie.
- `EChart` mantiene una instancia por contenedor, actualiza sus opciones, observa el tamaño mediante `ResizeObserver` y agrupa los ajustes con `requestAnimationFrame`. Al desmontarse cancela el frame, desconecta el observador y ejecuta `dispose()`.
- Los contenedores inicialmente sin dimensiones esperan hasta poder renderizar. Las tarjetas pequeñas permiten desplazamiento en el contenido para mantener visibles los datos de demostración.
- Tooltips confinados al contenedor con `renderMode: richText`; leyendas con desplazamiento y texto accesible con categorías y valores.
- Estados de carga, datos vacíos, datos incompatibles y fallo de inicialización/renderizado.
- README, topbar y pantalla de inicio actualizados a la FASE 6.

## Incidencias corregidas

### Persistencia del grid

La prueba de navegador dibujaba los tres gráficos, pero el primer redimensionado no enviaba la actualización del layout. Los callbacks originales consultaban el estado local desde un updater de React, que podía conservar el layout anterior al finalizar la operación.

Se utiliza directamente el layout final recibido en `onDragStop` y `onResizeStop`, sin efectos dentro del updater. La prueba confirma una sola petición al terminar cada operación y ninguna durante el arrastre.

### Compatibilidad de las pruebas con Python 3.12

La suite fallaba durante la colección porque varios tipos de anotaciones se importaban solo dentro de `TYPE_CHECKING`. Se añadió `from __future__ import annotations` a `conftest.py`, `test_auth.py`, `test_dashboards.py` y `test_widgets.py`. No se modificó la lógica de la API.

## Verificaciones ejecutadas

Entorno: Python 3.12.14 y Node.js 24.19.0.

| Verificación | Resultado |
| --- | --- |
| Backend: `python -m pytest -q` | 174 pruebas aprobadas |
| Alembic: `upgrade head` sobre SQLite temporal | Aplicadas las migraciones existentes |
| Alembic: `check` sobre SQLite temporal | Sin operaciones de actualización pendientes |
| Uvicorn + `GET /api/v1/health` | HTTP 200, `{"status":"ok"}` |
| Frontend: `npm run lint` | Aprobado |
| Frontend: `npm run typecheck` | Aprobado |
| Frontend: `npm run build` | Aprobado con las rutas existentes |
| Frontend: `npm run test:e2e` | 2 pruebas aprobadas |
| `git diff --check` | Sin errores de espacios |

Las pruebas de frontend cubren:

1. Rechazo de series desalineadas, valores no finitos y sectores negativos; aceptación del cero en barras.
2. Renderizado de los tres gráficos, comprobando píxeles dibujados en los canvases y las etiquetas de demostración.
3. Redimensionado del widget y ajuste del ancho real del canvas al contenedor.
4. Una actualización al finalizar resize y una al finalizar drag; ninguna durante el movimiento de drag.
5. Restauración del layout devuelto por la API tras recargar.
6. Adaptación a un cambio del ancho de la ventana.
7. Eliminación de un widget y recarga sin canvases duplicados ni errores de JavaScript.

## Límites

- La prueba de navegador usa respuestas HTTP simuladas: no verifica el flujo integral de autenticación ni la persistencia real en SQLite. Las 174 pruebas de backend sí se ejecutaron sobre una base temporal migrada.
- La validación completa del grid con la API real, incluido un fallo de guardado, sigue pendiente de la FASE 5.
- El navegador usado fue Chromium Headless Shell 134, disponible mediante `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`. La descarga del navegador predeterminado de Playwright falló en este entorno; se utilizó un ejecutable compatible alternativo.
- No se verificaron otros navegadores ni una auditoría de accesibilidad completa.
- Backend conserva dos advertencias de deprecación de Starlette/httpx y passlib/crypt; no impiden ejecutar la suite.
- KPI y tabla mantienen sus estados provisionales. Los gráficos muestran ejemplos fijos; obtener datos reales requiere las FASES 7 y 8.

## Migraciones y endpoints

No se añadieron migraciones, cambios de esquema ni endpoints. `GET /api/v1/widgets/{id}/data` continúa pendiente de fuentes de datos y query engine.

## Cómo probar localmente

1. Seguir el README para iniciar FastAPI y Next.js e iniciar sesión.
2. Abrir un dashboard y añadir widgets de barras, líneas y circular.
3. Comprobar gráficos, leyendas, tooltips y la etiqueta visible de demostración.
4. Arrastrar y redimensionar los widgets; recargar para comprobar el layout.
5. Ejecutar desde `frontend/`: `npx playwright install chromium` y `npm run test:e2e`.

## Siguiente fase

**FASE 7 — Data Sources**. La fase no se inició como parte de este cambio.

Commit: `feat(charts): integrate ECharts widgets for phase 6`.
