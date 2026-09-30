"""Endpoints de dashboards.

Las rutas solo traducen HTTP: la lógica de negocio vive en
``app/services/dashboard_service.py`` y las consultas en el repositorio.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas.dashboard import (
    DEFAULT_PAGE_SIZE,
    MAXIMUM_PAGE_SIZE,
    DashboardCreate,
    DashboardPage,
    DashboardRead,
    DashboardUpdate,
)
from app.services import dashboard_service
from app.services.dashboard_service import DashboardNotFoundError, EmptyDashboardError

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@contextmanager
def _domain_errors_as_http() -> Iterator[None]:
    """Traduce los errores de dominio a respuestas HTTP.

    Centralizarlo evita repetir el mismo bloque try/except en cada ruta que
    toca un dashboard.
    """
    try:
        yield
    except DashboardNotFoundError as error:
        # 404 y no 403: un 403 confirmaría que el identificador existe.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": error.code, "message": error.message},
        ) from None
    except EmptyDashboardError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": error.code, "message": error.message},
        ) from None


@router.get("", response_model=DashboardPage)
async def list_dashboards(
    current_user: CurrentUser,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=MAXIMUM_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DashboardPage:
    items, total = await dashboard_service.list_dashboards(
        session, current_user.id, limit, offset
    )
    return DashboardPage(items=list(items), total=total, limit=limit, offset=offset)


@router.post("", response_model=DashboardRead, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    payload: DashboardCreate, current_user: CurrentUser, session: SessionDep
):
    dashboard = await dashboard_service.create_dashboard(session, current_user.id, payload)
    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardRead)
async def get_dashboard(dashboard_id: int, current_user: CurrentUser, session: SessionDep):
    with _domain_errors_as_http():
        return await dashboard_service.get_dashboard(session, dashboard_id, current_user.id)


@router.patch("/{dashboard_id}", response_model=DashboardRead)
async def update_dashboard(
    dashboard_id: int, payload: DashboardUpdate, current_user: CurrentUser, session: SessionDep
):
    with _domain_errors_as_http():
        return await dashboard_service.update_dashboard(
            session, dashboard_id, current_user.id, payload
        )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(dashboard_id: int, current_user: CurrentUser, session: SessionDep):
    with _domain_errors_as_http():
        await dashboard_service.delete_dashboard(session, dashboard_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
