# Dashboard Builder

Herramienta de Business Intelligence en desarrollo incremental. **FASE 6 implementada: gráficos ECharts**, sin Docker. Los gráficos de barras, líneas y circular se muestran con datos de demostración identificados. La prueba automatizada de navegador usa una API simulada; la validación integral con la API real sigue pendiente. Los widgets se arrastran y redimensionan en un lienzo de 12 columnas impulsado por `react-grid-layout`; la posición se persiste al soltar. Las fases anteriores cubren autenticación, dashboards y el modelo completo de widgets con aislamiento por usuario.

## Estado del proyecto

| Fase | Estado |
| --- | --- |
| 1 — Bootstrap local | Implementada |
| 2 — Autenticación | Implementada |
| 3 — Dashboards | Implementada |
| 4 — Widgets | Implementada |
| 5 — Dashboard Grid | Implementada; pendiente de validación interactiva en navegador |
| 6 — ECharts | Implementada con datos de demostración |
| 7 — Data Sources | Pendiente; siguiente fase |
| 8 — Query Engine | Pendiente |
| 9 — Widget Builder | Pendiente |
| 10 — Dashboard profesional | Pendiente |

Los gráficos ECharts muestran ejemplos fijos con la etiqueta **Datos de demostración · Sin fuente conectada**. No representan la configuración ni métricas reales del usuario. Los KPI presentan `--` y las tablas conservan su espacio reservado. Las fuentes de datos y las consultas para obtener indicadores reales corresponden a las FASES 7 y 8.

## Requisitos

- Python 3.11 o superior (validado con Python 3.14).
- Node.js 20.9 o superior; recomendado Node.js 22 o 24 LTS.
- npm y dos terminales.

## Abrir en VS Code

```bash
cd dashboard_builder
code .
```

## 1. Configurar entorno

Desde la raíz del proyecto:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

En PowerShell puedes usar `Copy-Item` en lugar de `cp`.

Antes de arrancar, genera un secreto real y ponlo en `.env`:

```bash
openssl rand -hex 32
```

Pega el resultado en `JWT_SECRET_KEY`. La aplicación **no arranca** con la clave de ejemplo: exige al menos 32 caracteres. `.env` está en `.gitignore`; no lo subas ni compartas.

## 2. Backend — primera terminal

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

En Windows: `py -m venv .venv` y `.venv\Scripts\Activate.ps1`.

- API: http://localhost:8000/api/v1/health
- Documentación: http://localhost:8000/docs
- La ruta de health ejecuta `SELECT 1` para comprobar SQLite.

## 3. Crear el primer usuario

No existe registro público: los usuarios se crean en local. Con el backend parado o en marcha, desde `backend/`:

```bash
source .venv/bin/activate
python -m app.cli.create_user --email tu@empresa.com --full-name "Tu Nombre"
```

La contraseña se pide dos veces de forma interactiva, entre 8 y 72 caracteres. No la pases como argumento, porque quedaría en el historial del shell. Si el correo ya existe o la contraseña es débil, el comando falla con un mensaje y no escribe nada.

## 4. Frontend — segunda terminal

```bash
cd frontend
npm ci
npm run dev
```

Abre **http://localhost:3000/login**. Inicia sesión con el usuario creado; la raíz redirige a `/dashboards`.

Usa siempre `localhost`, no `127.0.0.1`: la cookie es same-site y el origen CORS configurado es `http://localhost:3000`.

## Rutas del frontend

| Ruta | Contenido |
| --- | --- |
| `/` | Redirige a `/dashboards` |
| `/dashboards` | Listado paginado, alta y borrado |
| `/dashboards/[id]` | Lienzo interactivo con drag & drop y resize de widgets |
| `/inicio` | Estado de la sesión y de la conexión |
| `/login` | Inicio de sesión |

Las páginas salvo `/login` exigen sesión; sin sesión redirigen a `/login`.

## Endpoints

```text
GET  /api/v1/health

POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me          (requiere cookie de sesión)

GET    /api/v1/dashboards       ?limit=20&offset=0
POST   /api/v1/dashboards
GET    /api/v1/dashboards/{id}
PATCH  /api/v1/dashboards/{id}
DELETE /api/v1/dashboards/{id}

GET    /api/v1/dashboards/{id}/widgets
POST   /api/v1/dashboards/{id}/widgets
PUT    /api/v1/dashboards/{id}/layouts   ← FASE 5: actualización de grid en lote
PATCH  /api/v1/widgets/{id}
DELETE /api/v1/widgets/{id}
```

`GET /api/v1/widgets/{id}/data` **todavía no existe**: sin fuentes de datos (FASE 7) ni query engine (FASE 8) no hay nada que devolver, y un endpoint que siempre falla sería peor que su ausencia.


El listado devuelve `{"items": [...], "total": N, "limit": L, "offset": O}`. `limit` va de 1 a 100 y `offset` de 0 en adelante; fuera de rango responde 422. El orden es por última modificación.

Un dashboard que no existe o que pertenece a otra cuenta responde **404** `DASHBOARD_NOT_FOUND`, nunca 403: un 403 confirmaría que el identificador existe. Lo mismo con `WIDGET_NOT_FOUND`.

## Widgets

Cinco tipos: `KPI`, `BAR_CHART`, `LINE_CHART`, `PIE_CHART` y `TABLE`.

El cuerpo acepta `type`, `title` (opcional), `configuration` y `layout`:

```json
{
  "type": "BAR_CHART",
  "title": "Ventas por mes",
  "configuration": {
    "dataset": "ventas",
    "dimension": "mes",
    "metric": "total",
    "aggregation": "sum"
  },
  "layout": { "x": 0, "y": 0, "w": 6, "h": 4 }
}
```

- `configuration` solo admite esas cuatro claves y una `aggregation` de la lista cerrada `sum`, `avg`, `count`, `min`, `max`, `distinct_count`. **No se acepta SQL ni texto libre.** La FASE 9 lo amplía al elegir dataset, dimensión, métrica y agregación desde la interfaz.
- `layout` exige las cuatro cifras y se guarda en columnas individuales (`x`, `y`, `w`, `h`). El grid actualiza las posiciones y tamaños en lote al finalizar el arrastre o el redimensionado, sin enviar peticiones durante cada movimiento.
- Si no se envía `layout`, el widget se coloca debajo del más bajo del dashboard, de modo que dos widgets seguidos no nazcan superpuestos. Si no se envía `title`, se usa el nombre del tipo.
- Un `PATCH` con `{}` responde 400 `WIDGET_EMPTY_PATCH`.
- En un `PATCH`, omitir `configuration` o `layout` los deja intactos, pero enviarlos a `null` es un 422: para vaciar la configuración se manda `{}`.
- `type` y `dashboard_id` no se pueden modificar: cambiarlos invalidaría la configuración guardada.

## Gráficos — FASE 6

- `ChartRenderer` selecciona barras, líneas o circular según el tipo del widget.
- Se importa `echarts/core` y se registran únicamente `BarChart`, `LineChart`, `PieChart`, `GridComponent`, `TooltipComponent`, `LegendComponent` y `CanvasRenderer`.
- Los gráficos se cargan de forma diferida solo en el cliente, sin inicializar canvas durante SSR.
- `ResizeObserver` ajusta el canvas cuando cambia el contenedor, incluido el redimensionado del grid. Al desmontarse se desconecta el observador y se libera la instancia con `dispose()`.
- `ChartData` define categorías y series numéricas ya preparadas para visualizar; no añade consultas ni opciones ECharts arbitrarias a la configuración persistida.
- Se contemplan carga, datos vacíos, valores incompatibles y fallos de renderizado. El texto accesible incluye los valores del gráfico.
- No se requieren migraciones ni endpoints nuevos.

Para probar: abre un dashboard, añade un widget de barras, uno de líneas y uno circular; comprueba sus etiquetas de demostración, leyendas y tooltips. Pulsa **Editar**, redimensiona y arrastra los widgets, y recarga para comprobar el layout.

## Interfaz y edición

- Barra lateral oscura, navegación por ruta, iconos Lucide y controles visuales consistentes.
- El dashboard abre en **Vista de lectura**. Pulsa **Editar** para mover, redimensionar o eliminar widgets; el layout se guarda al soltar. **Terminar edición** vuelve a la vista de lectura.
- **Añadir widget** abre el formulario y activa la edición. **Propiedades del dashboard** permite cambiar el nombre. El menú de opciones conserva la eliminación del dashboard con confirmación.
- En móviles la navegación se despliega desde el botón de menú. Por debajo de 640 px, la lectura apila las tarjetas a ancho completo sin modificar el layout guardado; la edición mantiene el lienzo de 12 columnas.
- Login, listado y estado del sistema comparten el estilo. Las fuentes de datos siguen pendientes y los gráficos conservan la etiqueta de demostración.

Validación del rediseño: [VALIDACION-UI.md](validaciones/VALIDACION-UI.md).

## Configuración

`.env` (raíz):

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/dashboard.db` | Rutas relativas se resuelven desde `backend/` |
| `FRONTEND_URL` | `http://localhost:3000` | Origen permitido por CORS |
| `APP_ENV` | `development` | Con `production` la cookie añade `Secure` |
| `JWT_SECRET_KEY` | — | **Obligatoria**, mínimo 32 caracteres |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Duración de la sesión |
| `SESSION_COOKIE_NAME` | `dashboard_builder_session` | Nombre de la cookie |
| `SESSION_COOKIE_SAMESITE` | `lax` | `lax`, `strict` o `none` |
| `SESSION_COOKIE_PATH` | `/` | Ámbito de la cookie |
| `SESSION_COOKIE_DOMAIN` | vacío | Solo si sirves el frontend en otro dominio |

`frontend/.env.local`:

| Variable | Por defecto |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` |

## Seguridad de la sesión

- Contraseñas con bcrypt (12 rondas) mediante `passlib`; nunca en texto plano.
- La API rechaza contraseñas de más de 72 caracteres: bcrypt ignoraría el resto en silencio.
- El JWT va en una cookie `httpOnly`, `SameSite=lax` y `Secure` cuando `APP_ENV=production`. **Nunca** se guarda en `localStorage`.
- El token solo se acepta por cookie. Un `Authorization: Bearer` no autentica.
- Login responde siempre con el mismo código y mensaje, exista o no la cuenta, e iguala el tiempo de verificación para no permitir enumerar usuarios.
- Un usuario desactivado responde igual que una contraseña incorrecta.
- `/api/v1/auth/me` es la referencia de endpoint protegido.
- Cada consulta de dashboards se filtra por el usuario de la sesión. El propietario lo impone el servidor: un `user_id` en el cuerpo de la petición se rechaza con 422.
- Los campos desconocidos en un payload se rechazan con 422 en lugar de ignorarse en silencio.

## Validaciones

Backend:

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
alembic current
alembic check
```

Las pruebas aplican las migraciones sobre una base temporal y **nunca** tocan `backend/data/dashboard.db`. `conftest.py` incluye una comprobación que falla si la configuración se leyó antes de fijar `DATABASE_URL`.

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
npm start
```

`backend/requirements-lock.txt` fija las versiones exactas del entorno validado, incluidas las de pruebas. `requirements.txt` contiene sólo dependencias directas de ejecución.

### Validación registrada de la FASE 5

El [informe de la FASE 5](validaciones/VALIDACION-FASE5.md) registra 174 pruebas de backend aprobadas, `alembic check` sin cambios pendientes y las comprobaciones de frontend `lint`, `typecheck` y `build` aprobadas. Estos resultados corresponden al informe existente; no constituyen una nueva ejecución de pruebas por esta actualización del README.

**Pendiente:** el informe indica que no se verificó el flujo interactivo en un navegador. Para cerrar la validación de la fase:

1. Iniciar sesión, crear un dashboard y agregar varios widgets.
2. Arrastrar un widget mediante su control de arrastre y comprobar que la posición se guarda al soltar.
3. Redimensionar un widget y comprobar que el tamaño se guarda al terminar.
4. Recargar la página y confirmar que se restauran las posiciones y tamaños.
5. Provocar un fallo de guardado, por ejemplo deteniendo temporalmente la API, y comprobar el mensaje de error y la coherencia del lienzo al restablecer la conexión.

### Validación de la FASE 6

Consulta el [informe de la FASE 6](validaciones/VALIDACION-FASE6.md) para los resultados y límites de la verificación.

Pruebas automatizadas del frontend (no usan la base de datos ni requieren iniciar FastAPI):

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

Playwright inicia Next.js en `http://localhost:3100`. La prueba de navegador simula las respuestas HTTP de la API para comprobar los gráficos, el redimensionado, el arrastre, la restauración del layout y la eliminación. No verifica persistencia real en SQLite ni el flujo completo de autenticación. Si ya tienes un Chromium compatible, puedes indicar su ejecutable mediante `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`.

## Estructura

- `backend/app/api/routes/`: endpoints HTTP (`health.py`, `auth.py`, `dashboards.py`, `widgets.py`).
- `backend/app/api/deps.py`: dependencias compartidas, incluida `get_current_user`.
- `backend/app/core/`: configuración, conexión SQLAlchemy async y `security.py` (bcrypt + JWT).
- `backend/app/models/`, `schemas/`, `repositories/`, `services/`: capas por responsabilidad.
- `backend/app/cli/create_user.py`: alta local de usuarios.
- `backend/alembic/`: migraciones versionadas.
- `backend/tests/`: pruebas de infraestructura, autenticación, dashboards y widgets.
- `frontend/app/`: App Router, `dashboards/`, `inicio/`, `login/`, `providers.tsx` con SWR.
- `frontend/components/`: `app-shell.tsx`, `require-auth.tsx`, `home-view.tsx`, `health-status.tsx`.
- `frontend/components/dashboard/dashboard-grid.tsx`: lienzo de 12 columnas con arrastre, redimensionado y persistencia.
- `frontend/components/widgets/widget-card.tsx`: tarjeta de widget con control de arrastre, gráficos de demostración y estados provisionales de KPI/tabla.
- `frontend/components/charts/`: `ChartRenderer`, barras, líneas, circular y ciclo de vida compartido de ECharts.
- `frontend/lib/echarts.ts`, `frontend/lib/chart-demo-data.ts` y `frontend/types/charts.ts`: registro modular, ejemplos y contrato de datos.
- `frontend/tests/charts.spec.ts`: validación de datos y pruebas del dashboard en Chromium.
- `frontend/hooks/`: `useAuth.ts` (sesión), `useDashboards.ts` y `useWidgets.ts` (listados y mutaciones).
- `frontend/lib/`: `api.ts` (comunicaciones HTTP), `fetcher.ts` (SWR) y `dashboard-pagination.ts` (estado de la lista paginada).
- `validaciones/`: informe de verificación de cada fase.
- `AGENTS.md`: reglas de arquitectura, alcance y roadmap.

## Problemas habituales

- **`JWT_SECRET_KEY` demasiado corta:** genera una con `openssl rand -hex 32` y reinicia.
- **La sesión no se conserva al recargar:** estás abriendo `127.0.0.1:3000` en lugar de `localhost:3000`, o el backend corre con otro `FRONTEND_URL`.
- **Cierra sesión al instante:** el tiempo del sistema o `ACCESS_TOKEN_EXPIRE_MINUTES` es 0. Comprueba el valor.
- **No conecta con la API:** verifica uvicorn en el puerto 8000 y la variable del frontend.
- **No existe la base:** ejecuta `alembic upgrade head` antes de iniciar el backend.
- **Falta el usuario de prueba:** no hay registro público; usa `python -m app.cli.create_user`.
- **«Dashboard no encontrado» con una sesión válida:** ese dashboard no es tuyo. Comprueba con qué cuenta iniciaste sesión.

## Próxima fase

**FASE 7 — Data Sources**: crear la abstracción de fuentes de datos y conectar únicamente las fuentes previstas para esa fase. Preparar la arquitectura para CSV, Excel, SQLite y futuras conexiones.

La obtención de datos agregados para los widgets se completará con el motor de consultas seguro de la FASE 8. Hasta entonces, los gráficos mantienen ejemplos identificados.

La validación integral de la FASE 5 con la API real, incluido el comportamiento ante errores de guardado, sigue pendiente; la FASE 6 incorpora pruebas de navegador con una API simulada.

No se versionó `.env`, `.venv`, `node_modules` ni la base de datos de ejecución.
