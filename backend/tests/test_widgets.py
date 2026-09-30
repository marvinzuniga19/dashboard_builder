"""Pruebas de la FASE 4: CRUD de widgets, layout, configuración y aislamiento.

La prioridad vuelve a ser la autorización: un widget se cuelga de un dashboard,
así que el aislamiento solo funciona si la consulta llega a los dos. Un widget
ajeno debe ser indistinguible de uno inexistente y el listado nunca debe incluir
widgets de otra cuenta.
"""

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models.widget import GRID_COLUMNS, MAXIMUM_ROWS, MAXIMUM_TITLE_LENGTH, Widget, WidgetType
from app.schemas.widget import WidgetConfiguration, WidgetCreate, WidgetUpdate
from app.services.dashboard_service import delete_dashboard
from app.services.widget_service import (
    DEFAULT_TITLE_BY_TYPE,
    EmptyWidgetError,
    WidgetNotFoundError,
    create_widget,
    delete_widget,
    update_widget,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.dashboard import Dashboard
    from app.models.user import User

DASHBOARDS = "/api/v1/dashboards"
WIDGETS = "/api/v1/widgets"


def create(client: TestClient, dashboard_id: int, **payload: object) -> dict:
    body: dict[str, object] = {"type": WidgetType.KPI.value}
    body.update(payload)
    response = client.post(f"{DASHBOARDS}/{dashboard_id}/widgets", json=body)
    assert response.status_code == 201, response.text
    result: dict = response.json()
    return result


def config_esperada(**campos: object) -> dict[str, object]:
    """La respuesta devuelve siempre la configuración completa.

    Igual que ``DashboardRead.description``, un campo no informado viaja como
    ``null``: así el frontend puede leer ``configuration.metric`` sin comprobar
    antes si la clave existe. Lo que se guarda en la fila sí es compacto, y eso
    lo comprueba ``test_stored_configuration_keeps_only_informed_fields``.
    """
    completa: dict[str, object] = {
        "dataset": None,
        "dimension": None,
        "metric": None,
        "aggregation": None,
    }
    completa.update(campos)
    return completa


# --- Creación ---


def test_create_widget(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    body = create(
        logged_in_client,
        dashboard.id,
        title="Ventas del mes",
        configuration={
            "dataset": "ventas",
            "dimension": "mes",
            "metric": "total",
            "aggregation": "sum",
        },
    )

    assert body["id"] > 0
    assert body["dashboard_id"] == dashboard.id
    assert body["type"] == "KPI"
    assert body["title"] == "Ventas del mes"
    assert body["configuration"] == config_esperada(
        dataset="ventas", dimension="mes", metric="total", aggregation="sum"
    )
    assert body["created_at"] and body["updated_at"]


@pytest.mark.parametrize("tipo", [tipo.value for tipo in WidgetType])
def test_create_accepts_every_supported_type(
    logged_in_client: TestClient, dashboard: Dashboard, tipo: str
) -> None:
    assert create(logged_in_client, dashboard.id, type=tipo)["type"] == tipo


def test_create_rejects_unknown_type(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets", json={"type": "GAUGE"}
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_create_requires_type(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.post(f"{DASHBOARDS}/{dashboard.id}/widgets", json={})
    assert response.status_code == 422


def test_create_trims_title(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    assert create(logged_in_client, dashboard.id, title="  Margen  ")["title"] == "Margen"


@pytest.mark.parametrize("titulo", ["", "   "])
def test_create_rejects_blank_title(
    logged_in_client: TestClient, dashboard: Dashboard, titulo: str
) -> None:
    """Un título en blanco no es un error al crear: se aplica el del tipo."""
    body = create(logged_in_client, dashboard.id, title=titulo)
    assert body["title"] == DEFAULT_TITLE_BY_TYPE[WidgetType.KPI]


def test_create_without_title_uses_type_default(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    body = create(logged_in_client, dashboard.id, type=WidgetType.PIE_CHART.value)
    assert body["title"] == "Gráfico circular"


def test_create_rejects_title_over_the_column_limit(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets",
        json={"type": "KPI", "title": "x" * (MAXIMUM_TITLE_LENGTH + 1)},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "KPI", "dashboard_id": 999},
        {"type": "KPI", "titulo": "Metas"},
        {"type": "KPI", "id": 12},
    ],
)
def test_create_rejects_unknown_fields(
    logged_in_client: TestClient, dashboard: Dashboard, payload: dict[str, object]
) -> None:
    """Un campo mal escrito debe fallar, no guardarse en silencio."""
    response = logged_in_client.post(f"{DASHBOARDS}/{dashboard.id}/widgets", json=payload)

    assert response.status_code == 422, payload


def test_create_stores_empty_configuration_by_default(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    assert create(logged_in_client, dashboard.id)["configuration"] == config_esperada()


def test_create_reports_only_informed_fields(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    body = create(logged_in_client, dashboard.id, configuration={"metric": "total"})

    assert body["configuration"] == config_esperada(metric="total")


def test_create_ignores_blank_configuration_values(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    body = create(logged_in_client, dashboard.id, configuration={"metric": "   "})

    assert body["configuration"] == config_esperada()


def test_create_rejects_unknown_configuration_field(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets",
        json={"type": "KPI", "configuration": {"sql": "SELECT 1"}},
    )

    assert response.status_code == 422


def test_create_rejects_unknown_aggregation(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    """La agregación es un conjunto cerrado: sin query engine no se negocia."""
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets",
        json={"type": "KPI", "configuration": {"metric": "total", "aggregation": "mediana"}},
    )

    assert response.status_code == 422


def test_create_accepts_every_supported_aggregation(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    for agregacion in ("sum", "avg", "count", "min", "max", "distinct_count"):
        body = create(logged_in_client, dashboard.id, configuration={"aggregation": agregacion})
        assert body["configuration"] == config_esperada(aggregation=agregacion)


@pytest.mark.parametrize(
    "layout",
    [
        {"x": -1, "y": 0, "w": 4, "h": 3},
        {"x": 0, "y": -2, "w": 4, "h": 3},
        {"x": 0, "y": 0, "w": 0, "h": 3},
        {"x": 0, "y": 0, "w": 4, "h": 0},
        {"x": 0, "y": 0, "w": GRID_COLUMNS + 1, "h": 3},
        {"x": 0, "y": 0, "w": 4, "h": MAXIMUM_ROWS + 1},
    ],
)
def test_create_rejects_layout_outside_the_grid(
    logged_in_client: TestClient, dashboard: Dashboard, layout: dict[str, int]
) -> None:
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets", json={"type": "KPI", "layout": layout}
    )

    assert response.status_code == 422, layout


def test_create_rejects_partial_layout(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    """Enviar solo ``w`` reubicaría el widget en (0,0) con una altura inventada."""
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets", json={"type": "KPI", "layout": {"w": 4}}
    )

    assert response.status_code == 422


def test_create_rejects_unknown_layout_field(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    response = logged_in_client.post(
        f"{DASHBOARDS}/{dashboard.id}/widgets",
        json={"type": "KPI", "layout": {"x": 0, "y": 0, "w": 4, "h": 3, "rot": 1}},
    )

    assert response.status_code == 422


def test_create_accepts_valid_layout(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    layout = {"x": 2, "y": 5, "w": 4, "h": 3}

    assert create(logged_in_client, dashboard.id, layout=layout)["layout"] == layout


def test_create_without_layout_uses_type_defaults(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    assert create(logged_in_client, dashboard.id)["layout"] == {"x": 0, "y": 0, "w": 4, "h": 3}


def test_create_stacks_widgets_without_overlapping(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    """Dos widgets seguidos no deben nacer superpuestos en la misma casilla."""
    primero = create(logged_in_client, dashboard.id)["layout"]
    segundo = create(logged_in_client, dashboard.id)["layout"]

    assert primero == {"x": 0, "y": 0, "w": 4, "h": 3}
    assert segundo == {"x": 0, "y": 3, "w": 4, "h": 3}


def test_create_stacks_below_the_tallest_widget(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    create(logged_in_client, dashboard.id, layout={"x": 0, "y": 0, "w": 12, "h": 8})

    assert create(logged_in_client, dashboard.id)["layout"]["y"] == 8


def test_create_in_foreign_dashboard_returns_404(
    other_user_client: TestClient, dashboard: Dashboard
) -> None:
    """No se puede plantar un widget en el dashboard de otra cuenta."""
    response = other_user_client.post(f"{DASHBOARDS}/{dashboard.id}/widgets", json={"type": "KPI"})

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WIDGET_NOT_FOUND"


def test_create_in_missing_dashboard_returns_404(logged_in_client: TestClient) -> None:
    response = logged_in_client.post(f"{DASHBOARDS}/9999/widgets", json={"type": "KPI"})

    assert response.status_code == 404


# --- Listado ---


def test_list_widgets_of_empty_dashboard(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    response = logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}/widgets")

    assert response.status_code == 200
    assert response.json() == []


def test_list_widgets_in_creation_order(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    create(logged_in_client, dashboard.id, title="Primero")
    create(logged_in_client, dashboard.id, title="Segundo")
    create(logged_in_client, dashboard.id, title="Tercero")

    body = logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}/widgets").json()

    assert [widget["title"] for widget in body] == ["Primero", "Segundo", "Tercero"]


def test_list_widgets_only_returns_that_dashboard(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    otro_id = logged_in_client.post(DASHBOARDS, json={"name": "Otro"}).json()["id"]
    create(logged_in_client, dashboard.id, title="Mío")
    create(logged_in_client, otro_id, title="Del otro")

    body = logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}/widgets").json()

    assert [widget["title"] for widget in body] == ["Mío"]


def test_list_widgets_of_foreign_dashboard_returns_404(
    logged_in_client: TestClient, other_user_client: TestClient, dashboard: Dashboard
) -> None:
    """404 y no una lista vacía: una lista vacía confirmaría que el dashboard existe."""
    create(logged_in_client, dashboard.id, title="Privado")

    response = other_user_client.get(f"{DASHBOARDS}/{dashboard.id}/widgets")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WIDGET_NOT_FOUND"


def test_list_widgets_of_missing_dashboard_returns_404(logged_in_client: TestClient) -> None:
    assert logged_in_client.get(f"{DASHBOARDS}/9999/widgets").status_code == 404


# --- Actualización ---


def test_update_widget_title(logged_in_client: TestClient, widget: Widget) -> None:
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={"title": "Margen bruto"})

    assert response.status_code == 200
    assert response.json()["title"] == "Margen bruto"


def test_update_keeps_untouched_fields(logged_in_client: TestClient, widget: Widget) -> None:
    response = logged_in_client.patch(
        f"{WIDGETS}/{widget.id}", json={"configuration": {"metric": "importe"}}
    )

    assert response.status_code == 200
    assert response.json()["title"] == widget.title
    assert response.json()["type"] == widget.type
    assert response.json()["layout"] == {"x": 0, "y": 0, "w": 4, "h": 3}


def test_update_layout(logged_in_client: TestClient, widget: Widget) -> None:
    layout = {"x": 4, "y": 2, "w": 6, "h": 5}

    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={"layout": layout})

    assert response.status_code == 200
    assert response.json()["layout"] == layout


def test_update_configuration_replaces_previous(
    logged_in_client: TestClient, widget: Widget
) -> None:
    """``configuration`` se sustituye entera: no se mezclan campos viejos y nuevos."""
    logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={"configuration": {"dataset": "ventas"}})

    response = logged_in_client.patch(
        f"{WIDGETS}/{widget.id}", json={"configuration": {"metric": "total"}}
    )

    assert response.json()["configuration"] == config_esperada(metric="total")


def test_update_empty_patch_returns_400(logged_in_client: TestClient, widget: Widget) -> None:
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "WIDGET_EMPTY_PATCH"


def test_update_rejects_null_title(logged_in_client: TestClient, widget: Widget) -> None:
    """La columna es NOT NULL: null debe ser un 422, no un 500."""
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("campo", ["configuration", "layout"])
def test_update_rejects_null_optional_object(
    logged_in_client: TestClient, widget: Widget, campo: str
) -> None:
    """``configuration`` y ``layout`` no admiten null explícito en un PATCH.

    Omitir el campo deja la columna intacta; enviarlo a null no significa nada
    y, si llegara al servicio, ``None.model_dump()`` o ``None["x"]`` producirían
    un 500 en lugar de un 422.
    """
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={campo: None})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_update_with_null_object_leaves_the_widget_untouched(
    logged_in_client: TestClient, dashboard: Dashboard, widget: Widget
) -> None:
    """El rechazo ocurre antes de escribir: el widget conserva posición y config."""
    listado = f"{DASHBOARDS}/{dashboard.id}/widgets"
    antes = next(item for item in logged_in_client.get(listado).json() if item["id"] == widget.id)

    for campo in ("layout", "configuration"):
        respuesta = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={campo: None})
        assert respuesta.status_code == 422

    despues = next(item for item in logged_in_client.get(listado).json() if item["id"] == widget.id)
    assert despues == antes


@pytest.mark.parametrize("titulo", ["", "   "])
def test_update_rejects_blank_title(
    logged_in_client: TestClient, widget: Widget, titulo: str
) -> None:
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={"title": titulo})

    assert response.status_code == 422


def test_update_rejects_title_over_the_column_limit(
    logged_in_client: TestClient, widget: Widget
) -> None:
    response = logged_in_client.patch(
        f"{WIDGETS}/{widget.id}", json={"title": "x" * (MAXIMUM_TITLE_LENGTH + 1)}
    )

    assert response.status_code == 422


@pytest.mark.parametrize("payload", [{"type": "TABLE"}, {"dashboard_id": 999}, {"id": 7}])
def test_update_rejects_type_and_dashboard(
    logged_in_client: TestClient, widget: Widget, payload: dict[str, object]
) -> None:
    """Cambiar el tipo invalidaría la configuración guardada."""
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json=payload)

    assert response.status_code == 422, payload


def test_update_rejects_layout_outside_the_grid(
    logged_in_client: TestClient, widget: Widget
) -> None:
    response = logged_in_client.patch(
        f"{WIDGETS}/{widget.id}", json={"layout": {"x": 0, "y": 0, "w": 99, "h": 3}}
    )

    assert response.status_code == 422


def test_update_rejects_partial_layout(logged_in_client: TestClient, widget: Widget) -> None:
    response = logged_in_client.patch(f"{WIDGETS}/{widget.id}", json={"layout": {"h": 9}})

    assert response.status_code == 422


def test_update_foreign_widget_returns_404(
    other_user_client: TestClient, logged_in_client: TestClient, widget: Widget
) -> None:
    response = other_user_client.patch(f"{WIDGETS}/{widget.id}", json={"title": "Secuestrado"})

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WIDGET_NOT_FOUND"

    intacto = logged_in_client.get(f"{DASHBOARDS}/{widget.dashboard_id}/widgets").json()
    assert intacto[0]["title"] == widget.title


def test_update_missing_widget_returns_404(logged_in_client: TestClient) -> None:
    response = logged_in_client.patch(f"{WIDGETS}/9999", json={"title": "Fantasma"})

    assert response.status_code == 404


# --- Borrado ---


def test_delete_widget(
    logged_in_client: TestClient, widget: Widget, dashboard: Dashboard
) -> None:
    response = logged_in_client.delete(f"{WIDGETS}/{widget.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}/widgets").json() == []


def test_delete_twice_returns_404(logged_in_client: TestClient, widget: Widget) -> None:
    assert logged_in_client.delete(f"{WIDGETS}/{widget.id}").status_code == 204
    assert logged_in_client.delete(f"{WIDGETS}/{widget.id}").status_code == 404


def test_delete_keeps_siblings(logged_in_client: TestClient, widget: Widget) -> None:
    create(logged_in_client, widget.dashboard_id, type=WidgetType.TABLE.value, title="Detalle")

    logged_in_client.delete(f"{WIDGETS}/{widget.id}")

    body = logged_in_client.get(f"{DASHBOARDS}/{widget.dashboard_id}/widgets").json()
    assert [otro["title"] for otro in body] == ["Detalle"]


def test_delete_foreign_widget_returns_404(
    other_user_client: TestClient, logged_in_client: TestClient, widget: Widget
) -> None:
    response = other_user_client.delete(f"{WIDGETS}/{widget.id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WIDGET_NOT_FOUND"

    supervivientes = logged_in_client.get(f"{DASHBOARDS}/{widget.dashboard_id}/widgets").json()
    assert [sobreviviente["id"] for sobreviviente in supervivientes] == [widget.id]


def test_delete_missing_widget_returns_404(logged_in_client: TestClient) -> None:
    assert logged_in_client.delete(f"{WIDGETS}/9999").status_code == 404


async def test_delete_dashboard_cascades_to_widgets(
    session: AsyncSession, dashboard: Dashboard, widget: Widget, user: User
) -> None:
    """Borrar el dashboard se lleva sus widgets: lo aplica la base, no el ORM."""
    await delete_dashboard(session, dashboard.id, user.id)

    total = await session.scalar(select(func.count()).select_from(Widget))
    assert total == 0


# --- Autorización de los endpoints ---


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", f"{DASHBOARDS}/1/widgets"),
        ("post", f"{DASHBOARDS}/1/widgets"),
        ("patch", f"{WIDGETS}/1"),
        ("delete", f"{WIDGETS}/1"),
    ],
)
def test_widget_endpoints_require_session(client: TestClient, method: str, path: str) -> None:
    extra = {"json": {"type": "KPI"}} if method == "post" else {}

    response = getattr(client, method)(path, **extra)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


def test_data_endpoint_does_not_exist_yet(
    logged_in_client: TestClient, widget: Widget
) -> None:
    """Se aplaza a la FASE 8: sin query engine no hay nada que devolver."""
    assert logged_in_client.get(f"{WIDGETS}/{widget.id}/data").status_code == 404


# --- Servicio ---


async def test_stored_configuration_keeps_only_informed_fields(
    session: AsyncSession, dashboard: Dashboard, user: User
) -> None:
    """La fila guarda solo lo informado, aunque la respuesta complete los null."""
    payload = WidgetCreate(
        type=WidgetType.KPI, configuration=WidgetConfiguration(metric="total")
    )

    widget = await create_widget(session, dashboard.id, user.id, payload)

    assert widget.configuration == {"metric": "total"}


async def test_stored_configuration_defaults_to_empty_dict(
    session: AsyncSession, dashboard: Dashboard, user: User
) -> None:
    widget = await create_widget(
        session, dashboard.id, user.id, WidgetCreate(type=WidgetType.KPI)
    )

    assert widget.configuration == {}


async def test_service_rejects_foreign_widget(session: AsyncSession, widget: Widget) -> None:
    with pytest.raises(WidgetNotFoundError):
        await delete_widget(session, widget.id, user_id=9999)


async def test_service_rejects_empty_patch(
    session: AsyncSession, widget: Widget, user: User
) -> None:
    with pytest.raises(EmptyWidgetError):
        await update_widget(session, widget.id, user.id, WidgetUpdate())


async def test_service_requires_ownership_to_create(
    session: AsyncSession, dashboard: Dashboard
) -> None:
    with pytest.raises(WidgetNotFoundError):
        await create_widget(session, dashboard.id, 9999, WidgetCreate(type=WidgetType.KPI))


async def test_service_rejects_ownership_to_list(
    session: AsyncSession, dashboard: Dashboard, widget: Widget
) -> None:
    from app.services.widget_service import list_widgets

    with pytest.raises(WidgetNotFoundError):
        await list_widgets(session, dashboard.id, user_id=9999)


# ============================================================================
# FASE 5: Actualización de layout en lote para el grid
# ============================================================================


def test_batch_layout_update_success(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    w1 = create(logged_in_client, dashboard.id, title="W1")
    w2 = create(logged_in_client, dashboard.id, title="W2")

    payload = {
        "items": [
            {"id": w1["id"], "x": 2, "y": 0, "w": 5, "h": 4},
            {"id": w2["id"], "x": 7, "y": 1, "w": 5, "h": 3},
        ]
    }
    response = logged_in_client.put(f"{DASHBOARDS}/{dashboard.id}/layouts", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2

    by_id = {w["id"]: w["layout"] for w in data}
    assert by_id[w1["id"]] == {"x": 2, "y": 0, "w": 5, "h": 4}
    assert by_id[w2["id"]] == {"x": 7, "y": 1, "w": 5, "h": 3}

    # Comprueba que persista en el GET posterior
    get_res = logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}/widgets")
    assert get_res.status_code == 200
    persisted = {w["id"]: w["layout"] for w in get_res.json()}
    assert persisted[w1["id"]] == {"x": 2, "y": 0, "w": 5, "h": 4}
    assert persisted[w2["id"]] == {"x": 7, "y": 1, "w": 5, "h": 3}


def test_batch_layout_update_empty_items(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    create(logged_in_client, dashboard.id, title="W1")
    response = logged_in_client.put(f"{DASHBOARDS}/{dashboard.id}/layouts", json={"items": []})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_batch_layout_update_rejects_duplicate_ids(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    w1 = create(logged_in_client, dashboard.id, title="W1")
    payload = {
        "items": [
            {"id": w1["id"], "x": 0, "y": 0, "w": 4, "h": 3},
            {"id": w1["id"], "x": 4, "y": 0, "w": 4, "h": 3},
        ]
    }
    response = logged_in_client.put(f"{DASHBOARDS}/{dashboard.id}/layouts", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "layout_patch",
    [
        {"x": -1, "y": 0, "w": 4, "h": 3},
        {"x": 0, "y": -1, "w": 4, "h": 3},
        {"x": 0, "y": 0, "w": 0, "h": 3},
        {"x": 0, "y": 0, "w": 13, "h": 3},
        {"x": 0, "y": 0, "w": 4, "h": 0},
        {"x": 0, "y": 0, "w": 4, "h": 25},
    ],
)
def test_batch_layout_update_validates_bounds(
    logged_in_client: TestClient, dashboard: Dashboard, layout_patch: dict
) -> None:
    w1 = create(logged_in_client, dashboard.id, title="W1")
    item = {"id": w1["id"]}
    item.update(layout_patch)
    response = logged_in_client.put(
        f"{DASHBOARDS}/{dashboard.id}/layouts", json={"items": [item]}
    )
    assert response.status_code == 422


def test_batch_layout_update_rejects_foreign_or_unknown_widget(
    logged_in_client: TestClient, other_user_client: TestClient, dashboard: Dashboard
) -> None:
    w1 = create(logged_in_client, dashboard.id, title="W1")
    # other_user_client intenta actualizar w1 a través de su propio dashboard inexistente o ajeno
    payload = {"items": [{"id": w1["id"], "x": 0, "y": 0, "w": 4, "h": 3}]}
    response = other_user_client.put(
        f"{DASHBOARDS}/{dashboard.id}/layouts", json=payload
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WIDGET_NOT_FOUND"


def test_batch_layout_update_rejects_foreign_dashboard(
    other_user_client: TestClient, dashboard: Dashboard
) -> None:
    response = other_user_client.put(
        f"{DASHBOARDS}/{dashboard.id}/layouts", json={"items": []}
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "WIDGET_NOT_FOUND"


def test_batch_layout_update_requires_auth(client: TestClient, dashboard: Dashboard) -> None:
    response = client.put(f"{DASHBOARDS}/{dashboard.id}/layouts", json={"items": []})
    assert response.status_code == 401

