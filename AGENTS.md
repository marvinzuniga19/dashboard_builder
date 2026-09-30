# AGENTS.md

# Dashboard Builder

Este archivo contiene las instrucciones permanentes para cualquier agente de IA que trabaje sobre este repositorio.

Antes de modificar código, lee este archivo completo y respeta sus reglas.

---

## 1. Objetivo

Construir una aplicación web llamada **Dashboard Builder** que permita crear, editar y visualizar dashboards de negocio mediante widgets configurables.

Será conceptualmente similar a una versión simplificada de Power BI.

Debe permitir progresivamente:

- Crear, editar y eliminar dashboards.
- Crear y configurar widgets.
- Mover widgets mediante drag & drop.
- Redimensionar widgets.
- Crear KPIs.
- Crear gráficos.
- Crear tablas.
- Conectar fuentes de datos.
- Configurar consultas.
- Aplicar filtros.
- Persistir layouts.
- Visualizar información de negocio.

La prioridad es:

1. Correctitud.
2. Seguridad.
3. Legibilidad.
4. Mantenibilidad.
5. Simplicidad.
6. Rendimiento.

Evitar sobreingeniería.

---

# 2. Stack obligatorio

## Backend

Utilizar:

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 async
- aiosqlite
- Alembic
- Pydantic v2
- python-jose
- passlib[bcrypt]
- pandas
- uvicorn

SQLAlchemy debe ser **asíncrono desde el inicio**.

Utilizar:

```python
async def
await
AsyncSession
create_async_engine
```

No introducir SQLAlchemy síncrono.

---

# 3. Base de datos

Utilizar inicialmente:

```text
SQLite
```

SQLite almacenará principalmente:

- usuarios
- dashboards
- widgets
- layouts
- configuraciones
- fuentes de datos
- consultas guardadas
- filtros
- permisos
- metadatos

La arquitectura debe permitir migrar posteriormente:

```text
SQLite → PostgreSQL
```

sin reescribir la lógica de negocio.

En cada conexión SQLite configurar:

```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
```

No depender innecesariamente de funcionalidades exclusivas de SQLite.

---

# 4. Frontend

Utilizar:

- Next.js 14+
- App Router
- TypeScript
- TailwindCSS
- SWR
- ECharts
- react-grid-layout

TypeScript debe utilizar:

```text
strict: true
```

Evitar `any`.

Si excepcionalmente se necesita `any`, justificar su utilización.

---

# 5. Ejecución local

Este proyecto se ejecutará directamente en la máquina local.

**NO utilizar Docker ni Docker Compose.**

No crear:

```text
Dockerfile
docker-compose.yml
compose.yaml
.dockerignore
```

No agregar Docker como requisito del proyecto salvo que el usuario lo solicite explícitamente en el futuro.

## Backend

Crear un entorno virtual:

```bash
cd backend

python -m venv .venv
```

En Linux:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://localhost:8000
```

## Frontend

Instalar dependencias:

```bash
cd frontend
npm install
```

Ejecutar:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 6. Arquitectura

Respetar:

```text
Browser
   │
   ▼
Next.js
   │
   │ HTTP / JSON
   ▼
FastAPI
   │
   ├── Metadata DB
   │      SQLite
   │
   └── Data Sources
          ├── CSV
          ├── Excel
          ├── SQLite
          └── futuras fuentes
```

## Regla crítica

El frontend **NUNCA** accede directamente a la base de datos.

Toda operación debe pasar por FastAPI.

Next.js consume APIs HTTP.

---

# 7. Backend

FastAPI será responsable de:

- autenticación
- autorización
- usuarios
- dashboards
- widgets
- layouts
- fuentes de datos
- consultas
- filtros
- agregaciones
- transformación de datos
- validación
- permisos
- generación de datasets

El backend debe devolver datos preparados para visualización.

Evitar enviar filas crudas cuando el frontend solamente necesita información agregada.

Ejemplo:

```json
{
  "title": "Ventas mensuales",
  "xAxis": [
    "Enero",
    "Febrero",
    "Marzo"
  ],
  "series": [
    {
      "name": "Ventas",
      "type": "bar",
      "data": [
        12500,
        14800,
        17300
      ]
    }
  ]
}
```

---

# 8. Seguridad de consultas

Nunca ejecutar directamente SQL arbitrario enviado por el frontend.

El frontend debe describir consultas mediante estructuras controladas.

Ejemplo:

```json
{
  "dataset": "ventas",
  "dimensions": ["mes"],
  "metrics": [
    {
      "field": "total",
      "aggregation": "sum"
    }
  ],
  "filters": [],
  "sort": [],
  "limit": 100
}
```

El backend será responsable de convertir esta configuración en consultas seguras.

Validar:

- datasets
- campos
- dimensiones
- métricas
- agregaciones
- filtros
- ordenamientos
- límites

Utilizar parámetros/bind parameters.

Prevenir SQL injection.

---

# 9. Autenticación

Utilizar:

```text
JWT
```

El JWT principal debe almacenarse mediante:

```text
cookie httpOnly
```

No guardar el token principal en:

```text
localStorage
```

FastAPI debe configurar CORS con:

```python
allow_credentials=True
```

Configurar explícitamente los origins permitidos.

En desarrollo:

```text
http://localhost:3000
```

Las cookies deben considerar:

- HttpOnly
- Secure en producción
- SameSite
- Path
- expiración

Implementar progresivamente:

```text
login
logout
/api/v1/auth/me
```

---

# 10. Modelo de dominio

Entidades iniciales:

```text
User
Dashboard
Widget
DataSource
SavedQuery
```

Relación principal:

```text
User
 └── Dashboard
      └── Widget
```

Un Dashboard pertenece a un usuario.

Un Dashboard contiene múltiples Widgets.

Un Widget pertenece a un Dashboard.

---

# 11. Widgets

Tipos iniciales:

```text
KPI
BAR_CHART
LINE_CHART
PIE_CHART
TABLE
```

Diseñar el sistema para agregar nuevos tipos posteriormente.

Un widget debe almacenar conceptualmente:

```text
id
dashboard_id
type
title
configuration
layout
created_at
updated_at
```

`configuration` puede utilizar JSON.

Ejemplo:

```json
{
  "dataset": "ventas",
  "dimension": "mes",
  "metric": "total",
  "aggregation": "sum"
}
```

Layout:

```json
{
  "x": 0,
  "y": 0,
  "w": 4,
  "h": 3
}
```

Debe ser compatible con `react-grid-layout`.

---

# 12. Dashboard Grid

Utilizar:

```text
react-grid-layout
```

Permitir:

- drag
- resize
- persistencia
- restauración del layout

No enviar una petición HTTP durante cada pequeño movimiento.

Persistir:

- al finalizar drag
- al finalizar resize

o utilizar debounce cuando corresponda.

---

# 13. ECharts

Utilizar:

```typescript
echarts/core
```

No importar toda la librería.

Registrar solamente los componentes utilizados.

Ejemplo:

```text
BarChart
LineChart
PieChart
GridComponent
TooltipComponent
LegendComponent
CanvasRenderer
```

Mantener aproximadamente:

```text
components/
└── charts/
    ├── ChartRenderer.tsx
    ├── BarChart.tsx
    ├── LineChart.tsx
    └── PieChart.tsx
```

`ChartRenderer` seleccionará el componente correspondiente al tipo de widget.

---

# 14. Estructura del repositorio

Mantener aproximadamente:

```text
dashboard-builder/
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── dashboards.py
│   │   │       ├── widgets.py
│   │   │       ├── datasources.py
│   │   │       └── queries.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── data/
│   ├── tests/
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── dashboards/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   └── layout.tsx
│   │
│   ├── components/
│   │   ├── dashboard/
│   │   ├── widgets/
│   │   ├── charts/
│   │   └── ui/
│   │
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
├── .env.example
├── .gitignore
├── AGENTS.md
└── README.md
```

Se permiten modificaciones justificadas.

No mezclar responsabilidades únicamente para reducir la cantidad de archivos.

---

# 15. Arquitectura backend por capas

Mantener:

```text
routes
   ↓
services
   ↓
repositories
   ↓
SQLAlchemy
   ↓
database
```

## Routes

Responsables de:

- HTTP
- parámetros
- request
- response
- status codes
- dependencies

No colocar lógica compleja de negocio.

## Services

Responsables de:

- lógica de negocio
- coordinación
- validaciones de negocio

## Repositories

Responsables de:

- persistencia
- consultas SQLAlchemy
- acceso a datos

## Schemas

Responsables de:

- validación
- serialización
- contratos API

## Models

Responsables de:

- ORM
- relaciones

---

# 16. SQLAlchemy 2.0

Utilizar sintaxis moderna.

Preferir:

```python
select(Model)
```

Modelos:

```python
Mapped[]
mapped_column()
```

No utilizar APIs legacy salvo necesidad documentada.

---

# 17. Pydantic v2

Utilizar APIs modernas de Pydantic v2.

Para schemas ORM:

```python
model_config = ConfigDict(from_attributes=True)
```

No introducir patrones deprecated de Pydantic v1.

---

# 18. Alembic

Todos los cambios del esquema deben administrarse mediante Alembic.

No utilizar:

```python
Base.metadata.create_all()
```

como sistema habitual para administrar el esquema.

Cada cambio estructural debe generar una migración.

Comandos habituales:

```bash
cd backend

alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

# 19. API

Versionar mediante:

```text
/api/v1
```

Ejemplos:

```text
GET    /api/v1/health

POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

GET    /api/v1/dashboards
POST   /api/v1/dashboards
GET    /api/v1/dashboards/{id}
PATCH  /api/v1/dashboards/{id}
DELETE /api/v1/dashboards/{id}

POST   /api/v1/dashboards/{id}/widgets
PATCH  /api/v1/widgets/{id}
DELETE /api/v1/widgets/{id}

GET    /api/v1/widgets/{id}/data
```

Utilizar status codes HTTP apropiados.

---

# 20. Manejo de errores

Mantener respuestas consistentes.

Ejemplo:

```json
{
  "detail": {
    "code": "DASHBOARD_NOT_FOUND",
    "message": "Dashboard not found"
  }
}
```

Nunca exponer stack traces al frontend en producción.

---

# 21. SWR

Centralizar comunicaciones HTTP.

Mantener aproximadamente:

```text
frontend/lib/
├── api.ts
└── fetcher.ts
```

Utilizar SWR para:

- usuario actual
- dashboards
- widgets
- datos de widgets

Considerar siempre:

```text
loading
error
empty
success
```

Evitar llamadas `fetch()` innecesariamente dispersas.

---

# 22. UI/UX

La aplicación debe sentirse como una herramienta profesional de Business Intelligence.

Priorizar:

- diseño moderno
- minimalismo
- claridad
- responsive design
- sidebar
- topbar
- navegación intuitiva
- workspace amplio
- tarjetas limpias
- jerarquía visual
- preparación para dark mode

Conceptualmente:

```text
┌─────────────────────────────────────────────┐
│ Topbar                                      │
├────────────┬────────────────────────────────┤
│            │                                │
│ Sidebar    │       Dashboard Canvas         │
│            │                                │
│ Dashboards │    KPI      KPI       KPI      │
│ Data       │                                │
│ Settings   │    ┌─────────────────────┐     │
│            │    │       Chart         │     │
│            │    └─────────────────────┘     │
│            │                                │
│            │    ┌─────────────────────┐     │
│            │    │       Table         │     │
│            │    └─────────────────────┘     │
└────────────┴────────────────────────────────┘
```

No sacrificar usabilidad por efectos visuales.

---

# 23. Rendimiento

Evitar:

- N+1 queries
- datasets gigantes innecesarios
- respuestas HTTP excesivas
- renders innecesarios
- bundles completos de ECharts
- peticiones constantes durante drag & drop
- transformaciones repetidas

Las agregaciones deben realizarse preferentemente en backend.

Utilizar pandas cuando realmente aporte valor.

---

# 24. Calidad del código

Python debe utilizar type hints.

TypeScript debe utilizar tipado estricto.

Utilizar nombres descriptivos.

Evitar:

- archivos gigantes
- funciones gigantes
- lógica duplicada
- comentarios obvios
- abstracciones prematuras
- sobreingeniería

Si una función asume demasiadas responsabilidades, dividirla.

---

# 25. Dependencias

Antes de agregar una dependencia:

1. Comprobar si realmente es necesaria.
2. Revisar si la funcionalidad ya existe.
3. Preferir dependencias mantenidas.
4. Evitar instalar paquetes para tareas triviales.

No actualizar dependencias importantes arbitrariamente durante tareas no relacionadas.

---

# 26. Variables de entorno

Mantener:

```text
.env.example
```

Nunca versionar:

```text
.env
```

Ejemplo:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/dashboard.db

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Nunca incluir secretos reales.

---

# 27. .gitignore

Como el proyecto se ejecutará localmente, ignorar correctamente como mínimo:

```text
# Environment
.env
.env.local

# Python
backend/.venv/
backend/__pycache__/
backend/**/*.pyc
backend/.pytest_cache/

# SQLite runtime files
backend/data/*.db
backend/data/*.db-shm
backend/data/*.db-wal

# Next.js
frontend/node_modules/
frontend/.next/
frontend/out/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

No ignorar migraciones Alembic.

---

# 28. Git

No ejecutar operaciones destructivas sin autorización.

No utilizar:

```bash
git push --force
git reset --hard
```

sin autorización explícita.

No:

- eliminar ramas arbitrariamente
- eliminar trabajo existente
- sobrescribir cambios del usuario
- modificar secretos
- agregar `.env`

Antes de modificar código comprobar el estado del repositorio cuando corresponda.

Al terminar una fase sugerir un Conventional Commit.

Ejemplo:

```bash
git commit -m "feat(dashboard): add widget grid persistence"
```

No realizar commits automáticamente salvo solicitud explícita.

---

# 29. Protección del código existente

Antes de crear algo:

1. Buscar si ya existe.
2. Leer la implementación.
3. Comprender sus dependencias.
4. Reutilizar lo existente cuando tenga sentido.

No reescribir archivos completos cuando basta un cambio localizado.

No eliminar código funcional simplemente porque existe otra forma de hacerlo.

---

# 30. Tests

Agregar pruebas progresivamente.

Priorizar:

- autenticación
- autorización
- dashboards
- widgets
- query engine
- agregaciones
- permisos

Cada bug importante corregido debería considerar un test de regresión.

---

# 31. Validaciones

Después de modificar código ejecutar las validaciones relevantes disponibles.

## Backend

```bash
cd backend

source .venv/bin/activate

pytest
```

Cuando corresponda:

```bash
alembic upgrade head
```

Comprobar que FastAPI inicia:

```bash
uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend

npm run lint
npm run build
```

Si existe un script específico:

```bash
npm run typecheck
```

No afirmar que una validación pasó si realmente no fue ejecutada.

---

# 32. Forma de trabajo

Trabajar incrementalmente.

Antes de modificar código:

1. Leer `AGENTS.md`.
2. Inspeccionar el repositorio.
3. Revisar archivos relacionados.
4. Comprender el estado actual.
5. Identificar el alcance.
6. Implementar solamente ese alcance.
7. Ejecutar validaciones.
8. Corregir errores introducidos.

No implementar fases futuras automáticamente.

No realizar refactors masivos durante tareas pequeñas.

---

# 33. Formato antes de cada fase

Antes de implementar presentar:

```text
FASE X — Nombre

Objetivo:
...

Estado actual:
...

Archivos que revisaré:
...

Archivos que probablemente modificaré:
...

Dependencias nuevas:
...

Riesgos:
...

Plan:
1. ...
2. ...
3. ...
```

Después proceder.

---

# 34. Formato al terminar una fase

Presentar:

```text
FASE X COMPLETADA

Implementado:
- ...

Archivos principales modificados:
- ...

Migraciones:
- ...

Validaciones ejecutadas:
- ...

Cómo probar:
1. ...
2. ...
3. ...

Problemas conocidos:
- ...

Siguiente fase recomendada:
FASE X+1 — ...

Commit sugerido:
git commit -m "..."
```

No declarar una fase completada si existen errores importantes sin resolver.

---

# 35. Roadmap

## FASE 1 — Bootstrap local

Implementar:

- estructura monorepo
- FastAPI
- Next.js
- TypeScript
- TailwindCSS
- entorno virtual Python
- requirements.txt
- configuración
- SQLite async
- SQLAlchemy 2
- PRAGMA WAL
- PRAGMA foreign_keys
- Alembic
- `.env.example`
- `.gitignore`
- health endpoint

No utilizar Docker.

Endpoint:

```text
GET /api/v1/health
```

Respuesta:

```json
{
  "status": "ok"
}
```

---

## FASE 2 — Autenticación

Implementar:

- User
- migración
- password hashing
- JWT
- cookies httpOnly
- login
- logout
- `/auth/me`
- protección de endpoints

---

## FASE 3 — Dashboards

Implementar:

- modelo Dashboard
- migración
- schemas
- repository
- service
- API CRUD
- listado frontend
- creación
- edición
- eliminación

---

## FASE 4 — Widgets

Implementar:

```text
KPI
BAR_CHART
LINE_CHART
PIE_CHART
TABLE
```

Agregar:

- modelo
- migración
- schemas
- repository
- service
- endpoints
- configuración básica

---

## FASE 5 — Dashboard Grid

Integrar:

```text
react-grid-layout
```

Implementar:

- drag
- resize
- persistencia
- restauración del layout

---

## FASE 6 — ECharts

Integrar:

```text
echarts/core
```

Agregar:

- bar chart
- line chart
- pie chart
- ChartRenderer

---

## FASE 7 — Data Sources

Crear abstracción:

```text
DataSource
```

Preparar arquitectura futura para:

```text
CSV
Excel
SQLite
PostgreSQL
MySQL
APIs
```

Implementar únicamente las fuentes requeridas en esta fase.

---

## FASE 8 — Query Engine

Crear sistema seguro para:

```text
dimensions
metrics
aggregations
filters
sort
limit
```

Nunca aceptar SQL arbitrario desde frontend.

---

## FASE 9 — Widget Builder

Crear interfaz visual para seleccionar:

```text
Dataset
Dimension
Metric
Aggregation
Chart Type
Filters
```

---

## FASE 10 — Dashboard profesional

Agregar progresivamente:

- filtros globales
- refresh
- edición mejorada
- duplicación
- responsive layout
- fullscreen
- loading states
- empty states
- error states
- mejoras UX

---

# 36. Primera ejecución

Si el repositorio está vacío comenzar exclusivamente con:

```text
FASE 1 — Bootstrap local
```

No implementar todavía:

- usuarios
- autenticación
- dashboards
- widgets
- ECharts
- react-grid-layout
- fuentes externas
- query engine

La primera meta es conseguir una infraestructura local limpia y estable.

## Backend

Crear entorno:

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Ejecutar migraciones:

```bash
alembic upgrade head
```

Levantar servidor:

```bash
uvicorn app.main:app --reload
```

Comprobar:

```text
GET http://localhost:8000/api/v1/health
```

Debe responder:

```json
{
  "status": "ok"
}
```

## Frontend

Ejecutar:

```bash
cd frontend

npm install
npm run dev
```

Comprobar:

```text
http://localhost:3000
```

El frontend debe cargar correctamente.

---

# 37. Regla para OpenCode

Cuando recibas una nueva instrucción:

**No empieces modificando código inmediatamente.**

Primero:

1. Lee `AGENTS.md`.
2. Ejecuta `git status`.
3. Inspecciona la estructura del repositorio.
4. Lee los archivos relevantes.
5. Determina el estado de la fase actual.
6. Detecta posibles conflictos arquitectónicos.
7. Presenta un plan breve.
8. Implementa solamente lo solicitado.
9. Ejecuta las validaciones relevantes.
10. Corrige errores introducidos por tus cambios.
11. Resume exactamente qué cambió.

No asumir que una fase está incompleta únicamente por su número. Inspeccionar primero el código existente.

Si una funcionalidad ya existe, revisarla antes de reemplazarla.

No implementar automáticamente la siguiente fase después de terminar una.

---

# 38. Regla de seguridad

Nunca inventar resultados.

No afirmar:

```text
Tests passed
Build successful
Migration successful
Server running correctly
```

si esas acciones no fueron realmente ejecutadas y verificadas.

Si un comando no puede ejecutarse, explicar:

- qué comando no pudo ejecutarse
- por qué
- qué falta
- cómo puede verificarlo el usuario

---

# 39. Regla final

La instrucción explícita más reciente del usuario tiene prioridad sobre este archivo.

Sin embargo, si una petición puede:

- romper arquitectura
- introducir una vulnerabilidad
- causar pérdida de datos
- romper compatibilidad
- destruir trabajo existente

debes advertirlo antes de realizar el cambio.

El objetivo no es escribir la mayor cantidad de código posible.

El objetivo es construir **Dashboard Builder** de forma incremental, segura, legible y mantenible.
