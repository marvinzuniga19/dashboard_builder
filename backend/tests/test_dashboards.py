"""Pruebas de la FASE 3: CRUD de dashboards, aislamiento entre usuarios y paginación.

La prioridad es la autorización: un dashboard ajeno debe ser indistinguible de uno
inexistente, y el listado nunca debe incluir datos de otra cuenta.
"""

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from app.models.dashboard import MAXIMUM_NAME_LENGTH, Dashboard
from app.schemas.dashboard import DashboardCreate, DashboardUpdate
from app.services.dashboard_service import (
    DashboardNotFoundError,
    EmptyDashboardError,
    create_dashboard,
    update_dashboard,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

DASHBOARDS = "/api/v1/dashboards"


def create(client: TestClient, name: str, description: str | None = None) -> dict:
    payload: dict[str, object] = {"name": name}
    if description is not None:
        payload["description"] = description
    response = client.post(DASHBOARDS, json=payload)
    assert response.status_code == 201, response.text
    body: dict = response.json()
    return body


# --- Creación ---


def test_create_dashboard(logged_in_client: TestClient, user: User) -> None:
    body = create(logged_in_client, "Ventas mensuales", "Resumen comercial")

    assert body["name"] == "Ventas mensuales"
    assert body["description"] == "Resumen comercial"
    assert body["id"] > 0
    assert body["created_at"] and body["updated_at"]
    # El propietario nunca se expone: el cliente solo conoce el dashboard, no su
    # dueño, y menos aún su identificador de usuario.
    assert "user_id" not in body


def test_create_dashboard_trims_whitespace(logged_in_client: TestClient) -> None:
    assert create(logged_in_client, "  Ventas  ")["name"] == "Ventas"


def test_create_dashboard_without_description_defaults_to_null(
    logged_in_client: TestClient,
) -> None:
    assert create(logged_in_client, "Sin descripción")["description"] is None


def test_empty_description_becomes_null(logged_in_client: TestClient) -> None:
    """Una cadena de espacios se normaliza a null en vez de guardarse como ``"   "``."""
    assert create(logged_in_client, "Vacía", "    ")["description"] is None


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_create_rejects_blank_name(logged_in_client: TestClient, name: str) -> None:
    response = logged_in_client.post(DASHBOARDS, json={"name": name})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_create_rejects_name_over_the_column_limit(logged_in_client: TestClient) -> None:
    response = logged_in_client.post(DASHBOARDS, json={"name": "x" * (MAXIMUM_NAME_LENGTH + 1)})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_create_rejects_unknown_fields(logged_in_client: TestClient) -> None:
    """``user_id`` en el payload no puede reasignar la propiedad del dashboard."""
    response = logged_in_client.post(
        DASHBOARDS, json={"name": "Intruso", "user_id": 999}
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


# --- Listado ---


def test_list_is_empty_for_a_new_account(logged_in_client: TestClient) -> None:
    body = logged_in_client.get(DASHBOARDS).json()

    assert body == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_list_returns_only_own_dashboards(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    body = logged_in_client.get(DASHBOARDS).json()

    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [dashboard.id]


def test_list_never_leaks_another_account(
    logged_in_client: TestClient, other_user_client: TestClient, dashboard: Dashboard
) -> None:
    """El dashboard de `user` no puede aparecer en el listado de `other_user`."""
    create(other_user_client, "Suyo")

    body = other_user_client.get(DASHBOARDS).json()

    assert body["total"] == 1
    assert dashboard.id not in [item["id"] for item in body["items"]]


def test_list_orders_by_most_recent_first(logged_in_client: TestClient) -> None:
    primero = create(logged_in_client, "Primero")
    segundo = create(logged_in_client, "Segundo")

    items = logged_in_client.get(DASHBOARDS).json()["items"]

    assert [item["id"] for item in items] == [segundo["id"], primero["id"]]


# --- Paginación ---


def test_pagination_splits_without_gaps_or_repeats(
    logged_in_client: TestClient, tied_timestamps: None
) -> None:
    """Regresión: `updated_at` tiene precisión de segundo en SQLite, así que sin
    el desempate por `id` dos dashboards creados en el mismo segundo podrían
    repetirse o saltarse al paginar."""
    primera = logged_in_client.get(DASHBOARDS, params={"limit": 2, "offset": 0}).json()
    segunda = logged_in_client.get(DASHBOARDS, params={"limit": 2, "offset": 2}).json()
    tercera = logged_in_client.get(DASHBOARDS, params={"limit": 2, "offset": 4}).json()

    assert primera["total"] == segunda["total"] == tercera["total"] == 5
    assert [len(page["items"]) for page in (primera, segunda, tercera)] == [2, 2, 1]

    vistos = [item["id"] for page in (primera, segunda, tercera) for item in page["items"]]
    assert len(vistos) == len(set(vistos)) == 5


def test_offset_beyond_the_end_returns_no_items(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    body = logged_in_client.get(DASHBOARDS, params={"offset": 500}).json()

    assert body["items"] == []
    # `total` sigue reflejando el número real: el frontend necesita saber que hay
    # contenido aunque la página pedida esté vacía.
    assert body["total"] == 1


def test_limit_and_offset_are_echoed(logged_in_client: TestClient) -> None:
    body = logged_in_client.get(DASHBOARDS, params={"limit": 5, "offset": 1}).json()

    assert body["limit"] == 5
    assert body["offset"] == 1


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "muchos"}],
)
def test_pagination_rejects_out_of_range_parameters(
    logged_in_client: TestClient, params: dict
) -> None:
    response = logged_in_client.get(DASHBOARDS, params=params)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


# --- Lectura ---


def test_get_returns_own_dashboard(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Ventas mensuales"


# --- Aislamiento entre usuarios ---


@pytest.mark.parametrize("method,payload", [("get", None), ("delete", None), ("patch", {"name": "X"})])
def test_other_account_dashboard_is_reported_as_missing(
    other_user_client: TestClient, dashboard: Dashboard, method: str, payload: dict | None
) -> None:
    """404 y no 403: un 403 confirmaría que el identificador existe."""
    url = f"{DASHBOARDS}/{dashboard.id}"
    response = other_user_client.request(method.upper(), url, json=payload)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DASHBOARD_NOT_FOUND"


async def test_other_account_dashboard_is_untouched_after_failed_attempts(
    session: AsyncSession, other_user_client: TestClient, dashboard: Dashboard
) -> None:
    """Los intentos en contra no deben alterar el dashboard de su propietario."""
    other_user_client.patch(f"{DASHBOARDS}/{dashboard.id}", json={"name": "Secuestrado"})
    other_user_client.delete(f"{DASHBOARDS}/{dashboard.id}")

    await session.refresh(dashboard)
    assert dashboard.name == "Ventas mensuales"


def test_unknown_id_is_reported_as_missing(logged_in_client: TestClient) -> None:
    response = logged_in_client.get(f"{DASHBOARDS}/987654")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DASHBOARD_NOT_FOUND"


# --- Actualización ---


def test_update_changes_the_name(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.patch(
        f"{DASHBOARDS}/{dashboard.id}", json={"name": "Ventas Q1"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Ventas Q1"


def test_update_only_touches_sent_fields(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    """``PATCH {"name": ...}`` no debe borrar la descripción."""
    logged_in_client.patch(f"{DASHBOARDS}/{dashboard.id}", json={"name": "Otro nombre"})

    body = logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}").json()

    assert body["name"] == "Otro nombre"
    assert body["description"] == "Resumen comercial"


def test_update_can_clear_description_with_null(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    """``exclude_unset`` distingue null explícito de campo omitido."""
    response = logged_in_client.patch(
        f"{DASHBOARDS}/{dashboard.id}", json={"description": None}
    )

    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["name"] == "Ventas mensuales"


def test_update_rejects_null_name(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    """`name` es NOT NULL: null debe ser un 422 controlado, no un 500."""
    response = logged_in_client.patch(f"{DASHBOARDS}/{dashboard.id}", json={"name": None})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_update_rejects_blank_name(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.patch(f"{DASHBOARDS}/{dashboard.id}", json={"name": "   "})

    assert response.status_code == 422
    assert logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}").json()["name"] == (
        "Ventas mensuales"
    )


def test_update_rejects_unknown_fields(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.patch(
        f"{DASHBOARDS}/{dashboard.id}", json={"user_id": 999}
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_update_without_fields_is_rejected(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    """Un PATCH vacío no es un no-op silencioso: sería más fácil de detectar como
    error del cliente que como un cambio que no ocurrió."""
    response = logged_in_client.patch(f"{DASHBOARDS}/{dashboard.id}", json={})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "DASHBOARD_EMPTY_PATCH"


# --- Borrado ---


def test_delete_removes_the_dashboard(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    response = logged_in_client.delete(f"{DASHBOARDS}/{dashboard.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert logged_in_client.get(f"{DASHBOARDS}/{dashboard.id}").status_code == 404


def test_delete_twice_reports_missing(logged_in_client: TestClient, dashboard: Dashboard) -> None:
    logged_in_client.delete(f"{DASHBOARDS}/{dashboard.id}")

    response = logged_in_client.delete(f"{DASHBOARDS}/{dashboard.id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DASHBOARD_NOT_FOUND"


# --- Autorización ---


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", DASHBOARDS),
        ("post", DASHBOARDS),
        ("get", f"{DASHBOARDS}/1"),
        ("patch", f"{DASHBOARDS}/1"),
        ("delete", f"{DASHBOARDS}/1"),
    ],
)
def test_every_endpoint_requires_a_session(client: TestClient, method: str, url: str) -> None:
    response = client.request(method.upper(), url, json={"name": "Sin sesión"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


# --- Servicio ---


async def test_create_dashboard_persists_for_the_owner(
    session: AsyncSession, user: User
) -> None:
    dashboard = await create_dashboard(
        session, user.id, DashboardCreate(name="  Informe  ", description="  ")
    )

    assert dashboard.name == "Informe"
    assert dashboard.description is None
    assert dashboard.user_id == user.id


async def test_update_service_raises_on_missing_dashboard(
    session: AsyncSession, user: User
) -> None:
    with pytest.raises(DashboardNotFoundError):
        await update_dashboard(session, 987654, user.id, DashboardUpdate(name="X"))


async def test_update_service_raises_on_empty_payload(
    session: AsyncSession, user: User, dashboard: Dashboard
) -> None:
    with pytest.raises(EmptyDashboardError):
        await update_dashboard(session, dashboard.id, user.id, DashboardUpdate())


# --- Integridad de la base de datos ---


async def test_deleting_a_user_cascades_to_dashboards(
    session: AsyncSession, user: User, dashboard: Dashboard
) -> None:
    """La cascada la aplica la base de datos (``ON DELETE CASCADE``), no el ORM, de
    modo que un ``delete()`` en bloque no deja dashboards huérfanos."""
    from sqlalchemy import delete, func, select

    from app.services.auth_service import create_user

    await create_user(session, "temporal@example.com", "contrasena-segura")
    victim = await session.scalar(
        select(User).where(User.email == "temporal@example.com")
    )
    await create_dashboard(session, victim.id, DashboardCreate(name="Se borra en cascada"))

    await session.execute(delete(User).where(User.id == victim.id))
    await session.commit()

    supervivientes = await session.scalar(
        select(func.count()).select_from(Dashboard).where(Dashboard.name == "Se borra en cascada")
    )
    assert supervivientes == 0
    # El dashboard de `user` sobrevive: la cascada es por usuario, no global.
    assert await session.get(Dashboard, dashboard.id) is not None


def test_dashboards_table_exists_in_the_test_schema(
    logged_in_client: TestClient, dashboard: Dashboard
) -> None:
    """El esquema de pruebas lo crea Alembic, no create_all: si la migración
    faltara, el listado fallaría al no encontrar la tabla."""
    assert logged_in_client.get(DASHBOARDS).json()["total"] == 1


@pytest.fixture(name="tied_timestamps")
async def tied_timestamps_fixture(
    logged_in_client: TestClient, session: AsyncSession
) -> None:
    """Cinco dashboards con el mismo `updated_at`.

    La API lo escribe sola, pero SQLite trunca a segundos: al crearlos seguidos es
    probable que compartan marca. Fijarla aquí hace el empate determinista en vez
    de depender de qué segundo cae la prueba.
    """
    import datetime as dt

    from sqlalchemy import select

    for index in range(5):
        create(logged_in_client, f"D{index}")

    shared_timestamp = dt.datetime(2026, 1, 1, 12, 0, 0)
    result = await session.execute(select(Dashboard))
    for dashboard in result.scalars().all():
        dashboard.updated_at = shared_timestamp
    await session.commit()


async def _all_dashboards(session: AsyncSession) -> list[Dashboard]:
    from sqlalchemy import select

    result = await session.execute(select(Dashboard))
    return list(result.scalars().all())
