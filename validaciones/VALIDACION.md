# Validación — FASE 2

## Resultado

Implementada la autenticación: modelo `User` con migración `0002_users`, hashing bcrypt, JWT en cookie httpOnly, `login` / `logout` / `me`, protección de endpoints mediante `get_current_user`, alta local de usuarios por CLI, pantalla de acceso en Next.js y protección de la página de inicio. Sin Docker.

## Entorno de validación

- Python 3.14.7, Node.js 26.10.0, npm 12.1.0.
- SQLite 3.53.4 mediante aiosqlite.
- `backend/requirements-lock.txt` y `frontend/package-lock.json` regenerados con las dependencias nuevas (`passlib`, `bcrypt`, `python-jose`, `email-validator`, `swr`).

## Verificaciones ejecutadas

### Backend

- `python -m pip install -r requirements.txt` y `-r requirements-dev.txt`: correcto.
- `python -m pytest -q`: **40 pruebas aprobadas**, con una advertencia de deprecación del adaptador TestClient/httpx de Starlette.
- `alembic upgrade head`: aplicadas `0001_bootstrap` y `0002_users`.
- `alembic current`: `0002_users (head)`.
- `alembic check`: no detectó nuevas operaciones de actualización.
- Esquema real inspeccionado en SQLite: tabla `users` e índice único `ix_users_email`.
- Uvicorn en `127.0.0.1:8000`: inició correctamente. `GET /api/v1/health` → **200** `{"status":"ok"}`.

Flujo HTTP real con `curl`:

| Paso | Resultado |
| --- | --- |
| `GET /auth/me` sin cookie | 401 `AUTH_REQUIRED` |
| `POST /auth/login` con contraseña incorrecta | 401 `AUTH_INVALID_CREDENTIALS` |
| `POST /auth/login` válido | 200, `Set-Cookie: …; HttpOnly; Max-Age=3600; Path=/; SameSite=lax` |
| `GET /auth/me` con la cookie | 200 con el usuario |
| `GET /auth/me` con `Authorization: Bearer` | 401 (la cookie es el único transporte) |
| `POST /auth/logout` | 200, cookie con `Max-Age=0` y `expires=1970` |
| `GET /auth/me` tras el cierre | 401 |

CORS comprobado con `Origin: http://localhost:3000`: el preflight responde con `access-control-allow-credentials: true` y el origen exacto; un origen no permitido no recibe `access-control-allow-origin`.

CLI comprobado sobre la base de ejecución: alta de `Demo@Example.com` normalizada a `demo@example.com` (id 1), segundo intento con el mismo correo rechazado y contraseña de menos de 8 caracteres rechazada.

### Frontend

- `npm run lint`: aprobado sin errores ni advertencias.
- `npm run typecheck`: aprobado.
- `npm run build`: aprobado con Next.js 16.3.7; rutas `/`, `/login` y `/_not-found`.
- `npm start` en el puerto 3000: `GET /` → **200**, `GET /login` → **200**.

## Incidencias encontradas y corregidas durante la fase

1. **`conftest.py` apuntaba a la base de datos de desarrollo.** Al añadir imports de `app` a nivel de módulo en el `conftest`, esos imports se ejecutaban antes de fijar `DATABASE_URL`, por lo que `build_engine()` leía el `.env` real. El `downgrade` de la sesión de pruebas eliminó la tabla `users` de `backend/data/dashboard.db`. Se corrigió moviendo todos los imports de la aplicación dentro de fixtures y se añadió una comprobación que aborta la suite si la configuración se resolvió antes de tiempo, más un test de regresión. La base de desarrollo se restauró con `alembic upgrade head` y se verificó que sobrevive a la suite.
2. **`Response.delete_cookie` de Starlette no fija la caducidad en el pasado.** `http.cookies` renderiza `expires=0` con la hora actual, de modo que la eliminación dependía únicamente de `Max-Age=0`. El cierre de sesión escribe ahora la caducidad de forma explícita (`1970-01-01T00:00:00Z`).
3. **Aviso deprecado de Alembic** al analizar `prepend_sys_path`: se añadió `path_separator = os` en `alembic.ini`.

## Límites de la validación

- **No se verificó el flujo en un navegador.** El entorno no tiene Chromium ni Playwright, igual que en la FASE 1. Las respuestas HTTP del frontend se comprobaron, pero no se comprobó de forma interactiva el envío del formulario, la persistencia de la cookie entre recargas ni el cambio de pantalla tras cerrar sesión.
- Como la página se autentica en el cliente, el HTML inicial de `/login` y de `/` muestra el estado de comprobación; el formulario aparece tras la hidratación en el navegador.
- `passlib` 1.7.4 registra `(trapped) error reading bcrypt version` al inicializar su backend bcrypt, porque `bcrypt` ya no expone `__about__`. El hashing y la verificación funcionan correctamente; la major de `bcrypt` está fijada a `<5.0` porque passlib no es compatible con la API de la 5.0.
- No hay límite de intentos de acceso: un atacante local podría probar contraseñas indefinidamente. Queda fuera del alcance de esta fase.
- La protección CSRF se apoya en `SameSite=lax` y en que CORS permite un único origen con credenciales. No se implementó un token de doble envío.
- `created_at` se devuelve sin desplazamiento horario porque SQLite almacena fechas sin zona; no afecta a la autenticación.

## Migraciones y alcance

`0002_users` crea la tabla de usuarios y el índice único del correo. El esquema se gestiona exclusivamente con Alembic; `conftest.py` aplica `upgrade head` sobre una base temporal y `downgrade base` al terminar.

Siguen pendientes las FASES 3 a 10: dashboards, widgets, grid, ECharts, fuentes de datos, query engine y widget builder. No se implementó registro público: los usuarios se crean con `python -m app.cli.create_user`. No se realizaron commits ni despliegue.

## Referencias técnicas consultadas

- [Password hashing con bcrypt](https://passlib.readthedocs.io/en/stable/names/bcrypt.html).
- [python-jose](https://python-jose.readthedocs.io/en/latest/).
- [Cookies httpOnly y SameSite](https://developer.mozilla.org/docs/Web/HTTP/Cookies).
- [Shared cookies y SameSite](https://web.dev/articles/samesite-cookies-explained).
