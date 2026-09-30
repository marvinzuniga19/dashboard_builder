"""Endpoints de widgets.

Las rutas solo traducen HTTP: la lógica de negocio vive en
``app/services/widget_service.py`` y las consultas en el repositorio.

``GET /widgets/{id}/data`` no existe todavía: sin fuentes de datos (FASE 7) ni
query engine (FASE 8) no hay nada que devolver, y un endpoint que siempre falla
sería peor que su ausencia.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas.widget import (
    DashboardLayoutUpdate,
    WidgetCreate,
    WidgetRead,
    WidgetUpdate,
)
from app.services import widget_service
from app.services.widget_service import EmptyWidgetError, WidgetNotFoundError

router = APIRouter(tags=["widgets"])


@contextmanager
def _domain_errors_as_http() -> Iterator[None]:
    """Traduce los errores de dominio a respuestas HTTP.

    Igual que en los dashboards: 404 en lugar de 403, para no confirmar que el
    identificador existe, y 400 cuando la petición no lleva nada que aplicar.
    """
    try:
        yield
    except WidgetNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": error.code, "message": error.message},
        ) from None
    except EmptyWidgetError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": error.code, "message": error.message},
        ) from None


@router.get(
    "/dashboards/{dashboard_id}/widgets",
    response_model=list[WidgetRead],
    summary="Lista los widgets de un dashboard",
)
async def list_widgets(
    dashboard_id: int, current_user: CurrentUser, session: SessionDep
) -> list[WidgetRead]:
    with _domain_errors_as_http():
        widgets = await widget_service.list_widgets(session, dashboard_id, current_user.id)
    return list(widgets)


@router.post(
    "/dashboards/{dashboard_id}/widgets",
    response_model=WidgetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un widget en un dashboard",
)
async def create_widget(
    dashboard_id: int, payload: WidgetCreate, current_user: CurrentUser, session: SessionDep
):
    with _domain_errors_as_http():
        return await widget_service.create_widget(session, dashboard_id, current_user.id, payload)


@router.put(
    "/dashboards/{dashboard_id}/layouts",
    response_model=list[WidgetRead],
    summary="Actualiza en lote las posiciones del grid del dashboard",
)
@router.patch(
    "/dashboards/{dashboard_id}/layouts",
    response_model=list[WidgetRead],
    summary="Actualiza en lote las posiciones del grid del dashboard",
)
async def update_dashboard_layouts(
    dashboard_id: int,
    payload: DashboardLayoutUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> list[WidgetRead]:
    with _domain_errors_as_http():
        widgets = await widget_service.update_dashboard_layouts(
            session, dashboard_id, current_user.id, payload
        )
    return list(widgets)


@router.patch("/widgets/{widget_id}", response_model=WidgetRead, summary="Actualiza un widget")
async def update_widget(
    widget_id: int, payload: WidgetUpdate, current_user: CurrentUser, session: SessionDep
):
    with _domain_errors_as_http():
        return await widget_service.update_widget(session, widget_id, current_user.id, payload)


@router.delete(
    "/widgets/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina un widget",
)
async def delete_widget(widget_id: int, current_user: CurrentUser, session: SessionDep):
    with _domain_errors_as_http():
        await widget_service.delete_widget(session, widget_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
