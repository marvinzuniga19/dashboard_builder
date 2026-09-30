# Validación — FASE 3

## Resultado

Implementados los dashboards: modelo `Dashboard` con migración `0003_dashboards`, capas `routes → services → repositories`, CRUD paginado bajo `/api/v1/dashboards` protegido por la cookie de sesión, y el frontend con `/dashboards`, `/dashboards/[id]` e `/inicio`. Sin Docker.

## Entorno de validación

- Python 3.14.7, Node.js 26.10.0, npm 12.1.0.
- SQLite 3.53.4 mediante aiosqlite.
- FastAPI 0.142.1, SQLAlchemy 2.0.54, Pydantic 2.13.5, Alembic 1.20.0, Next.js 16.3.7, React 19.3.
- Sin dependencias nuevas: `requirements.txt` y `package.json` no cambiaron.

## Verificaciones ejecutadas

### Backend

- `python -m pytest -q`: **85 pruebas aprobadas** (40 de las fases anteriores y 45 nuevas), con la misma advertencia de deprecación del adaptador TestClient/httpx de Starlette.
- `alembic upgrade head`: aplicada `0002_users → 0003_dashboards`.
- `alembic current`: `0003_dashboards (head)`.
- `alembic check`: **no detectó nuevas operaciones de actualización**, es decir, el modelo y el esquema coinciden.
- Las tres migraciones aplicadas en orden sobre una base nueva y vacía, sin errores.
- Esquema real inspeccionado en SQLite: tabla `dashboards`, índice `ix_dashboards_user_id` y clave foránea `user_id → users.id` con `ON DELETE CASCADE`.
- Uvicorn en `127.0.0.1:8125`: inició correctamente. `GET /api/v1/health` → **200** `{"status":"ok"}`.

Ciclo CRUD completo con `curl` sobre el servidor real:

| Paso | Resultado |
| --- | --- |
| `POST /auth/login` | 200, cookie de sesión |
| `GET /dashboards` sin elementos | 200 `{"items":[],"total":0,"limit":20,"offset":0}` |
| `POST /dashboards` con `"  Ventas mensuales  "` | 201, nombre **recortado** a `Ventas mensuales` |
| `PATCH /dashboards/1` con solo `name` | 200, `description` **conservada** |
| `PATCH` con `{"name": null}` | 422 `VALIDATION_ERROR` (no 500) |
| `PATCH` con `{}` | 400 `DASHBOARD_EMPTY_PATCH` |
| `POST` con `user_id` en el cuerpo | 422 `VALIDATION_ERROR` |
| `GET /dashboards?limit=101` y `?offset=-1` | 422 `VALIDATION_ERROR` |
| `DELETE /dashboards/1` | **204**, cuerpo de 0 bytes |
| `DELETE` repetido | 404 `DASHBOARD_NOT_FOUND` |

Aislamiento entre cuentas, comprobado con dos usuarios reales:

| Prueba | Resultado |
| --- | --- |
| Listado de Bruno tras 26 dashboards de Ana | `total=0` |
| `GET /dashboards/1` de Ana con sesión de Bruno | **404** `DASHBOARD_NOT_FOUND` |
| `PATCH` de Ana con sesión de Bruno | **404**, y el nombre no cambió |
| `DELETE` de Ana con sesión de Bruno | **404**, y el dashboard siguió existiendo |
| Los cinco endpoints sin cookie | 401 `AUTH_REQUIRED` |

Paginación con 26 dashboards reales: las páginas de 10, 10 y 6 devolvieron **26 identificadores únicos, sin huecos ni repeticiones**.

Cascada verificada con `PRAGMA foreign_keys=ON`: al eliminar el usuario propietario, sus 25 dashboards desaparecieron y los de otro usuario no se afectaron.

La base de ejecución del proyecto quedó intacta: `alembic_version` en `0003_dashboards`, el usuario `demo@example.com` conservado y la tabla `dashboards` vacía.

### Frontend

- `npm run lint`: aprobado sin errores ni advertencias.
- `npm run typecheck`: aprobado.
- `npm run build`: aprobado con Next.js 16.3.7; rutas `/`, `/_not-found`, `/dashboards`, `/dashboards/[id]` (dinámica), `/inicio` y `/login`.
- `npm start` en el puerto 3311:

| Ruta | HTTP |
| --- | --- |
| `/` | **307** con `location: /dashboards` |
| `/dashboards` | 200 |
| `/dashboards/1` | 200 |
| `/inicio` | 200 |
| `/login` | 200 |

Los chunks JS de la página se sirven con 200.

### Lógica de paginación del frontend

La decisión de qué estado mostrar está aislada en `frontend/lib/dashboard-pagination.ts` como función pura, y se ejecutó directamente con Node 26 (desactivación de tipos nativa) sobre **10 escenarios**, todos correctos: usuario sin dashboards, primera página, última página parcial, página fuera de rango, offset muy lejano, borrado total, offset no múltiplo del tamaño de página, página exacta, y prioridad de `loading` y `error`.

Se comprobó además que la comprobación **no es vacía**: la lógica anterior, con los mismos datos del escenario 4, produce `state="empty"` y la comprobación la rechaza.

```text
$ node /tmp/opencode/paginacion-check.ts
10 escenarios de paginación: OK
```

Esta verificación cubre la lógica, no el JSX: la rama `outOfRange` solo se alcanza con datos del cliente, y el prerender de `/dashboards` se ejecuta siempre en estado `loading` porque SWR no tiene respuesta durante la generación estática. Esa rama concreta está verificada por `tsc` y por ESLint, no en ejecución.

## Incidencias encontradas y corregidas durante la fase

1. **El modelo inicial declaraba relaciones a un `Widget` inexistente.** La primera versión de `app/models/dashboard.py` incluía `widgets` y `user.dashboards` para «dejar preparado» el modelo. `Widget` no existe hasta la FASE 4, y una relación sin clase ni atributo de contraparte rompe el mapeo de SQLAlchemy. Se eliminaron ambas relaciones: el borrado en cascada lo aplica la base con `ON DELETE CASCADE`, que además funciona con `delete()` en bloque, algo que la cascada del ORM no garantiza.

2. **Pydantic ignoraba en silencio los campos desconocidos.** Un `POST` con `user_id: 999` en el cuerpo devolvía **201**: el campo se descartaba sin avisar. La propiedad del dashboard nunca cambiaba (la impone la sesión), pero el contrato era ambiguo y un campo mal escrito desde el frontend se habría convertido en un no-op invisible. Se añadió `model_config = ConfigDict(extra="forbid")` a `DashboardCreate` y `DashboardUpdate`; los dos casos ahora devuelven 422. La ausencia de reasignación se comprobó antes de cambiar nada.

3. **`alembic revision --autogenerate` no respeta la convención de nombres.** `alembic.ini` no define `file_template`, así que generó `054809187645_dashboards.py`. Se renombró a `0003_dashboards.py` con su `revision` y `down_revision` ajustados, igual que `0001_bootstrap` y `0002_users`.

4. **Tres handlers repetían el mismo `try/except`.** El `404`/`400` estaba copiado en leer, actualizar y borrar. Se extrajo a un context manager `_domain_errors_as_http()`, y la suite completa se volvió a ejecutar después del cambio.

5. **El shell se renderizaba en el cliente, así que el HTML inicial no contenía el formulario.** No es un fallo de esta fase: es el comportamiento ya documentado en la FASE 2, porque la sesión se resuelve con SWR tras la hidratación. El HTML servido contiene «Comprobando sesión…».

6. **Un `await` dentro de una función síncrona en dos tests.** Los primeros borradores de la regresión de paginación y del aislamiento usaban la sesión async desde tests síncronos. Se corrigió moviendo la preparación de datos a una fixture async.

7. **Fichero `frontend/next-env.d.ts` regenerado por `next build`.** Next.js alterna la referencia a `.next/dev/types` según el comando ejecutado. Como es un archivo que administra la herramienta y el cambio no era intencionado, se revirtió con `git checkout`.

8. **Borrar el último dashboard de la última página dejaba la vista atrapada.** El hook decidía el estado con `items.length === 0`, así que al borrar los 5 últimos de 25 dashboards la API respondía `items: []` con `total: 20` (comportamiento ya cubierto por `test_offset_beyond_the_end_returns_no_items`) y la pantalla mostraba «Todavía no tienes dashboards», que es falso. Además la paginación solo se renderiza en el estado `success`, de modo que tampoco había forma de retroceder: había que recargar la página a mano. El backend ya distinguía bien ambos casos; el defecto estaba solo en el frontend. Se añadió el estado `outOfRange`, que explica lo ocurrido y ofrece «Volver a la página 1».

9. **La primera corrección quedaba mal y el lint la detectaba.** La solución inicial era corregir el `offset` dentro de un `useEffect`; la regla `react-hooks/set-state-in-effect` la marcó como error, con razón: provoca un render extra y oculta un salto de página. Se descartó ese enfoque —junto con la tentación de silenciar la regla con un `eslint-disable`— y se resolvió con el estado explícito, que además resulta más honesto para quien usa la aplicación.

10. **El enlace «Dashboards» no se marcaba activo en su propia página de detalle.** `pathname === item.href` fallaba en `/dashboards/1`, de modo que el detalle se veía como una pantalla sin sección activa. Ahora se compara por prefijo.

## Decisiones tomadas durante la fase

- **`/` redirige a `/dashboards`** y la pantalla informativa se conserva en `/inicio`. Ambas rutas aparecen en la navegación del shell, extraído a `app-shell.tsx` desde `home-view.tsx`.
- **`RequireAuth` monta los hijos solo con sesión válida**, para que sus hooks de SWR no disparen peticiones antes de resolver la sesión.
- **El listado devuelve un envelope** (`items`, `total`, `limit`, `offset`). Sin `total` el frontend no sabría si hay páginas siguientes.
- **`PATCH` con `{}` devuelve 400**, no un no-op: un cambio que no ocurre es más fácil de detectar como error del cliente que como un éxito silencioso.
- **Fuera de rango se explica, no se corrige solo.** Se prefirió un aviso con botón a un salto automático de página: el usuario ve qué ha pasado en lugar de que la lista cambie sola.

## Límites de la validación

- **No se verificó el flujo en un navegador.** El entorno no tiene Chromium ni Playwright, igual que en las fases anteriores. Se comprobaron las respuestas HTTP y que las rutas sirven, pero no la creación mediante el formulario, la navegación entre páginas ni el comportamiento de la paginación en pantalla.
- No se comprobó la reactividad visual ni el recorrido con teclado.
- **`allow_methods` del CORS no incluye `PUT`.** Es un desajuste preexistente de la FASE 2: `frontend/lib/api.ts` lo declaraba en su tipo `RequestOptions` aunque ningún endpoint lo usa. Se quitó del tipo para que un `PUT` futuro no falle en el preflight sin aviso. Ningún endpoint actual necesita `PUT`, así que no se tocó la configuración de CORS.
- Sin límite de intentos de acceso, ni token CSRF de doble envío: se mantienen las limitaciones ya documentadas en la FASE 2.
- Los tests tardan unos 45 s por el coste de bcrypt con 12 rondas en cada hash de contraseña de las fixtures.
- `created_at` y `updated_at` se devuelven sin desplazamiento horario porque SQLite almacena fechas sin zona.

## Migraciones y alcance

`0003_dashboards` crea la tabla de dashboards con su índice y la clave foránea en cascada. El esquema se gestiona solo con Alembic; `conftest.py` aplica `upgrade head` sobre una base temporal y `downgrade base` al terminar.

Siguen pendientes las FASES 4 a 10: widgets, grid con `react-grid-layout`, ECharts, fuentes de datos, query engine y widget builder. El lienzo del detalle está vacío a propósito y así lo indica la propia pantalla. No se añadieron rutas que requieran datos del servidor: el HTML inicial muestra el estado de comprobación de sesión.

## Referencias técnicas consultadas

- [Pydantic v2 — campos extra y `model_config`](https://docs.pydantic.dev/latest/concepts/models/#model-config).
- [Alembic — control de versiones y autogenerate](https://alembic.sqlalchemy.org/en/latest/).
- [SQLite — claves foráneas y `ON DELETE CASCADE`](https://www.sqlite.org/foreignkeys.html).
- [Next.js — App Router y rutas dinámicas](https://nextjs.org/docs/app/getting-started/project-structure).

## Referencias técnicas consultadas

- [Pydantic v2 — campos extra y `model_config`](https://docs.pydantic.dev/latest/concepts/models/#model-config).
- [Alembic — control de versiones y autogenerate](https://alembic.sqlalchemy.org/en/latest/).
- [SQLite — claves foráneas y `ON DELETE CASCADE`](https://www.sqlite.org/foreignkeys.html).
- [Next.js — App Router y rutas dinámicas](https://nextjs.org/docs/app/getting-started/project-structure).
