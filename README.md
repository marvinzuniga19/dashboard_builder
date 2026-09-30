# Dashboard Builder

Herramienta de Business Intelligence en desarrollo incremental. **FASE 2: autenticación**, sin Docker. Los usuarios se dan de alta con un comando local, la sesión viaja en una cookie httpOnly y la pantalla de inicio solo es visible con una sesión válida. Dashboards, widgets y gráficos aún no están implementados.

## Requisitos

- Python 3.11 o superior (validado con Python 3.14).
- Node.js 20.9 o superior; recomendado Node.js 22 o 24 LTS.
- npm y dos terminales.

## Abrir en VS Code

```bash
cd dashboard-builder
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

Abre **http://localhost:3000/login**. Inicia sesión con el usuario creado y entrarás en el inicio protegido.

Usa siempre `localhost`, no `127.0.0.1`: la cookie es same-site y el origen CORS configurado es `http://localhost:3000`.

## Endpoints

```text
GET  /api/v1/health
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me      (requiere cookie de sesión)
```

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

## Estructura

- `backend/app/api/routes/`: endpoints HTTP (`health.py`, `auth.py`).
- `backend/app/api/deps.py`: dependencias compartidas, incluida `get_current_user`.
- `backend/app/core/`: configuración, conexión SQLAlchemy async y `security.py` (bcrypt + JWT).
- `backend/app/models/`, `schemas/`, `repositories/`, `services/`: capas por responsabilidad.
- `backend/app/cli/create_user.py`: alta local de usuarios.
- `backend/alembic/`: migraciones versionadas.
- `backend/tests/`: pruebas de infraestructura y de autenticación.
- `frontend/app/`: App Router, `login/`, `providers.tsx` con SWR.
- `frontend/components/`: `home-view.tsx`, `health-status.tsx`.
- `frontend/hooks/useAuth.ts`: sesión actual, inicio y cierre de sesión.
- `frontend/lib/`: `api.ts` (comunicaciones HTTP) y `fetcher.ts` (SWR).
- `AGENTS.md`: reglas de arquitectura, alcance y roadmap.

## Problemas habituales

- **`JWT_SECRET_KEY` demasiado corta:** genera una con `openssl rand -hex 32` y reinicia.
- **La sesión no se conserva al recargar:** estás abriendo `127.0.0.1:3000` en lugar de `localhost:3000`, o el backend corre con otro `FRONTEND_URL`.
- **Cierra sesión al instante:** el tiempo del sistema o `ACCESS_TOKEN_EXPIRE_MINUTES` es 0. Comprueba el valor.
- **No conecta con la API:** verifica uvicorn en el puerto 8000 y la variable del frontend.
- **No existe la base:** ejecuta `alembic upgrade head` antes de iniciar el backend.
- **Falta el usuario de prueba:** no hay registro público; usa `python -m app.cli.create_user`.

## Próxima fase

**FASE 3 — Dashboards**: modelo Dashboard, migración, schemas, repository, service, API CRUD y listado, creación, edición y eliminación en el frontend.

Commit sugerido (no realizado):

```bash
git add .
git commit -m "feat(auth): add users, JWT session cookies and login flow"
```

No se Versionó `.env`, `.venv`, `node_modules` ni la base de datos de ejecución.
