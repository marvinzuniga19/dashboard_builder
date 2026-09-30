"""Reglas de negocio de dashboards.

El aislamiento entre usuarios vive aquí y en el repositorio: un dashboard ajeno
se trata como inexistente, nunca como "prohibido", porque responder 403 confirmaría
al atacante que ese identificador existe.
"""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard import Dashboard
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardCreate, DashboardUpdate


class DashboardNotFoundError(Exception):
    """El dashboard no existe o no pertenece al usuario."""

    code = "DASHBOARD_NOT_FOUND"
    message = "Dashboard no encontrado."


class EmptyDashboardError(Exception):
    """Una actualización sin campos aplicables no se ejecuta."""

    code = "DASHBOARD_EMPTY_PATCH"
    message = "Indica al menos un campo para actualizar."


async def _require_dashboard(
    repository: DashboardRepository, dashboard_id: int, user_id: int
) -> Dashboard:
    dashboard = await repository.get_for_user(dashboard_id, user_id)
    if dashboard is None:
        raise DashboardNotFoundError(DashboardNotFoundError.message)
    return dashboard


async def list_dashboards(
    session: AsyncSession, user_id: int, limit: int, offset: int
) -> tuple[Sequence[Dashboard], int]:
    return await DashboardRepository(session).list_for_user(user_id, limit, offset)


async def get_dashboard(
    session: AsyncSession, dashboard_id: int, user_id: int
) -> Dashboard:
    return await _require_dashboard(DashboardRepository(session), dashboard_id, user_id)


async def create_dashboard(
    session: AsyncSession, user_id: int, payload: DashboardCreate
) -> Dashboard:
    dashboard = Dashboard(user_id=user_id, name=payload.name, description=payload.description)
    return await DashboardRepository(session).add(dashboard)


async def update_dashboard(
    session: AsyncSession, dashboard_id: int, user_id: int, payload: DashboardUpdate
) -> Dashboard:
    repository = DashboardRepository(session)
    dashboard = await _require_dashboard(repository, dashboard_id, user_id)

    # exclude_unset distingue los campos omitidos de los enviados como null: es lo
    # que permite vaciar la descripción con `null` sin tocar el nombre.
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise EmptyDashboardError(EmptyDashboardError.message)

    for field, value in changes.items():
        setattr(dashboard, field, value)
    return await repository.update(dashboard)


async def delete_dashboard(session: AsyncSession, dashboard_id: int, user_id: int) -> None:
    repository = DashboardRepository(session)
    dashboard = await _require_dashboard(repository, dashboard_id, user_id)
    await repository.delete(dashboard)
