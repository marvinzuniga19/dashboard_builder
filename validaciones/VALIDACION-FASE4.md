# Validación — FASE 4

## Resultado

Widgets completos de extremo a extremo: modelo `Widget` con migración `0004_widgets`, capas `routes → services → repositories`, cuatro endpoints con el mismo aislamiento por usuario que los dashboards, `configuration` validada como estructura cerrada y `layout` en columnas listas para `react-grid-layout`. El detalle del dashboard permite crear, listar y borrar widgets. Sin drag, sin resize y sin gráficos: son las FASES 5 y 6.

## Entorno de validación

- Python 3.14.7, Node.js 26.10.0, SQLite 3.53.4.
- FastAPI 0.142.1, SQLAlchemy 2.0.54, Pydantic 2.13.5, Alembic 1.20.0, Next.js 16.3.7, React 19.3.
- Sin dependencias nuevas: `requirements.txt` y `package.json` no cambiaron.

## Verificaciones ejecutadas

### Backend

- `python -m pytest -q`: **162 pruebas aprobadas** (85 de las fases anteriores y **77 nuevas**), con la misma advertencia de deprecación del adaptador TestClient/httpx de Starlette.
- `alembic upgrade head`: aplicada `0003_dashboards → 0004_widgets`.
- `alembic current`: `0004_widgets (head)`.
- `alembic check`: **no detectó nuevas operaciones de actualización**.
- Ida y vuelta comprobada: `downgrade 0003_dashboards` y `upgrade head`.
- Esquema real inspeccionado en SQLite: `pragma foreign_key_list(widgets)` → `dashboards`, `ON DELETE CASCADE`.
- Uvicorn en `127.0.0.1:8126` con una base temporal y **dos cuentas reales**, una de cada lado del aislamiento.

Colocación automática y normalización:

| Caso | Resultado |
| --- | --- |
| `POST` sin `layout`, tipo `KPI` | 201, título «Indicador», layout `{x:0, y:0, w:4, h:3}` |
| Segundo `POST` sin `layout` | 201, layout `{x:0, y:3, w:6, h:4}`: apilado bajo el anterior, sin solaparse |
| `title` con espacios alrededor | 201, «Ventas por mes» sin espacios |
| `configuration` parcial | respuesta con la forma completa y los no informados a `null` |

Validaciones, todas **422 `VALIDATION_ERROR`** salvo donde se indica:

| Payload rechazado | Motivo |
| --- | --- |
| `{"type":"GAUGE"}` | Tipo fuera de la lista cerrada |
| `{"type":"KPI","layout":{"w":4}}` | Layout parcial: las cuatro cifras son obligatorias |
| `{"type":"KPI","layout":{...,"w":13,...}}` | Ancho mayor que las 12 columnas del grid |
| `{"type":"KPI","layout":{...,"rot":1}}` | Campo desconocido en el layout |
| `{"type":"KPI","configuration":{"sql":"SELECT 1"}}` | Campo desconocido: no se acepta SQL |
| `{"aggregation":"mediana"}` | Agregación fuera del conjunto cerrado |
| `{"titulo":"Metas"}` | Campo mal escrito, no se guarda en silencio |
| `{"dashboard_id":999}` | No se mueve un widget desde el cuerpo |
| `PATCH {"type":"TABLE"}` | El tipo no es modificable |
| `PATCH {"title":null}` | Columna NOT NULL: 422 y no un 500 |
| `PATCH {"configuration":null}` | Sin objeto que aplicar: 422 y no un 500 |
| `PATCH {"layout":null}` | Sin objeto que aplicar: 422 y no un 500 |

| Caso | Resultado |
| --- | --- |
| `PATCH {}` | **400** `WIDGET_EMPTY_PATCH` |
| Widget inexistente | **404** `WIDGET_NOT_FOUND` |
| Los cuatro endpoints sin cookie | **401** `AUTH_REQUIRED` |
| `GET /widgets/{id}/data` | **404**: endpoint aplazado a la FASE 8 |

Aislamiento, con la sesión de Bruno contra widgets de Ana: listar, crear, renombrar y borrar el widget de Ana respondieron los cuatro **404 `WIDGET_NOT_FOUND`**. Después de los cuatro intentos, los widgets de Ana seguían intactos con sus títulos originales, y sus dos `id` no habían cambiado.

Cascada verificada sobre la base real: al borrar el dashboard de Ana con `DELETE /api/v1/dashboards/1` (204), la tabla `widgets` quedó con **0 filas**.

### Frontend

- `npm run lint`: aprobado sin errores ni advertencias.
- `npm run typecheck`: aprobado.
- `npm run build`: aprobado; rutas `/`, `/_not-found`, `/dashboards`, `/dashboards/[id]` (dinámica), `/inicio` y `/login`.
- `npm start` en el puerto 3312:

| Ruta | HTTP |
| --- | --- |
| `/` | **307** con `location: /dashboards` |
| `/dashboards` | 200 |
| `/dashboards/1` | 200 |
| `/inicio` | 200 |
| `/login` | 200 |

## Incidencias encontradas y corregidas durante la fase

1. **La respuesta de `configuration` no coincide con lo que se guarda.** Las primeras pruebas fallaron al comparar el `configuration` devuelto con el enviado. Al investigar, el código tenía razón y la expectativa estaba mal: la fila almacena solo lo informado (`{"metric": "total"}`), pero `WidgetRead` vuelve a validar el dict y devuelve las cuatro claves, con `null` en las no informadas. Es el mismo criterio que ya usaba `DashboardRead.description`, y da al frontend una forma estable. Se corrigieron las pruebas y se añadieron dos que sí comprueban la fila: `test_stored_configuration_keeps_only_informed_fields` y `test_stored_configuration_defaults_to_empty_dict`.

2. **Un `title` en blanco en un `PATCH` habría causado un 500.** El validador convertía `""` y `"   "` en `None`, y `title` es NOT NULL: el `setattr` habría llegado a la base y fallen con un `IntegrityError`. En la creación el caso es legítimo (se aplica el nombre por defecto del tipo), pero en la actualización no hay título por defecto que aplicar. Ahora un título nulo o vacío al actualizar es un 422, con dos pruebas que lo cubren.

3. **`Layout` con valores por defecto habría reubicado los widgets al parchearlos.** Los cuatro campos tenían default (`x=0`, `y=0`, `h=4`…), de modo que un `PATCH {"layout":{"w":4}}` habría movido el widget al origen con una altura inventada. Se quitaron todos los valores por defecto y `layout` pasa a exigir las cuatro cifras; quien no lo envía, lo dice con `null` y entonces el servicio coloca el widget automáticamente.

4. **La fixture de `conftest` usaba `WidgetType` en tiempo de ejecución bajo `TYPE_CHECKING`.** Habría fallen con `NameError` en cuanto se usara. El import se movió al cuerpo de la fixture, como en las demás.

5. **`next-env.d.ts` volvió a cambiar** con `next build`, por el mismo motivo que en la FASE 3. Revertido con `git checkout`.

6. **`PATCH` con `configuration: null` o `layout: null` devolvía 500.** Es el fallo más serio de la fase, y lo encontró una revisión del servicio al cerrar la fase, no una prueba que ya existiera. El schema declaraba ambos campos como `WidgetConfiguration | None` y `Layout | None`, así que un null explícito pasaba la validación; el servicio lo recibía después y hacía `None.model_dump()` (`widget_service.py:110`) o `None["x"]` (`widget_service.py:113`). Los dos son `AttributeError` y `TypeError` sin capturar, es decir 500 con stack trace en producción, justo lo que AGENTS.md prohíbe.

   Se reprodujo primero, con pruebas que fallaron con esas dos excepciones, y luego se corrigió: un validador `before` rechaza el null explícito en el schema, igual que ya hacía con `title`. El campo omitido sigue dejando la columna intacta, porque los validadores no se ejecutan sobre los valores por defecto. Para vaciar la configuración se envía `{}`, que sí es un objeto válido.

   La causa de fondo era que el `None` de esos campos estaba pensado solo para "no informado" en la creación, pero `exclude_unset` no lo distingue de un null enviado a propósito, y esa confusión se coló en el `PATCH`.

   Tres pruebas nuevas: `test_update_rejects_null_optional_object` (parametrizada), `test_update_with_null_object_leaves_the_widget_untouched`, que además comprueba que el rechazo ocurre antes de escribir.

## Decisiones tomadas durante la fase

- **`configuration` tipada, no JSON libre.** Aceptar cualquier clave permitiría guardar basura que la FASE 8 tendría que sanear. Se valida la forma de AGENTS.md (`dataset`, `dimension`, `metric`, `aggregation`) y todo es opcional, porque el dataset todavía no existe.
- **`type` sin `CHECK` en la base.** AGENTS.md pide poder añadir tipos nuevos después; una restricción en la tabla obligaría a una migración cada vez que aparezca uno. La validación vive en Python, en `WidgetType`.
- **`layout` en columnas, no en un JSON.** La FASE 5 lo actualiza en cada fin de arrastre, y así se puede ordenar y filtrar en SQL. La API lo expone como objeto para ser compatible con react-grid-layout.
- **`GET /dashboards/{id}/widgets` no aparece en AGENTS.md**, pero sin él ni esta interfaz ni el grid de la FASE 5 pueden funcionar. AGENTS.md lo lista como ejemplos; queda como desviación declarada.
- **`GET /widgets/{id}/data` se aplaza.** Sin fuentes de datos ni query engine no hay nada que devolver. Crear un endpoint que responde siempre error sería peor que su ausencia.
- **Colocación automática al crear sin `layout`**: `x=0` y `y` igual a la suma de las alturas de los widgets del dashboard, con tamaño por defecto según el tipo.
- **Sin paginación en el listado de widgets**: la FASE 5 necesita el conjunto completo para montar el grid.
- **`type` y `dashboard_id` inmutables.** Cambiar el tipo invalidaría la configuración guardada; la FASE 9 resolverá el cambio sustituyendo el widget.

## Límites de la validación

- **No se verificó el flujo en un navegador.** El entorno no tiene Chromium ni Playwright, igual que en las fases anteriores. Se comprobaron las respuestas HTTP y que las rutas sirven, pero **no** la creación desde el formulario, la elección de tipo en el desplegable, el borrado con la confirmación ni la aparición de la lista.
- La lógica de la lista de widgets es idéntica a la de dashboards, que sí está cubierta por pruebas de backend, pero la vista de widgets no tiene pruebas propias: el frontend no tiene runner configurado y añadir uno sería una dependencia nueva.
- Sin límite de widgets por dashboard: el listado devuelve todo lo que cuelgue de él. Es lo que necesita el grid de la FASE 5, pero conviene revisarlo si un dashboard llega a cientos.
- `configuration` refleja la forma documentada en AGENTS.md, no una definitiva: la FASE 8 la ajustará al query engine real.
- Los tests tardan más de minuto en total por el coste de bcrypt con 12 rondas en cada hash de contraseña de las fixtures.
- `created_at` y `updated_at` se devuelven sin desplazamiento horario porque SQLite almacena fechas sin zona.

## Migraciones y alcance

`0004_widgets` crea la tabla con su índice por `dashboard_id` y la clave foránea en cascada, que encadena con la de `dashboards` sobre `users`: borrar un usuario elimina sus dashboards y, en cascada, sus widgets. El esquema se gestiona solo con Alembic; `conftest.py` aplica `upgrade head` sobre una base temporal y `downgrade base` al terminar.

Siguen pendientes las FASES 5 a 10: grid arrastrable, ECharts, fuentes de datos, query engine y widget builder.

## Referencias técnicas consultadas

- [SQLAlchemy 2.0 — columnas JSON](https://docs.sqlalchemy.org/en/20/orm/columns.html).
- [Alembic — control de versiones y autogenerate](https://alembic.sqlalchemy.org/en/latest/).
- [SQLite — claves foráneas y `ON DELETE CASCADE`](https://www.sqlite.org/foreignkeys.html).
- [Pydantic v2 — campos extra y `model_validator`](https://docs.pydantic.dev/latest/concepts/models/).
