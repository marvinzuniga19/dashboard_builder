"""Reglas de negocio de widgets.

Un widget ajeno se trata como inexistente, nunca como "prohibido", por el mismo
motivo que los dashboards: un 403 confirmaría que el identificador existe.
"""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.widget import Widget, WidgetType
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.widget_repository import WidgetRepository
from app.schemas.widget import DashboardLayoutUpdate, WidgetCreate, WidgetUpdate

# Títulos por defecto: un widget recién creado sin nombre debe ser identificable
# en el lienzo, no indistinguishable de los demás.
DEFAULT_TITLE_BY_TYPE: dict[WidgetType, str] = {
    WidgetType.KPI: "Indicador",
    WidgetType.BAR_CHART: "Gráfico de barras",
    WidgetType.LINE_CHART: "Gráfico de líneas",
    WidgetType.PIE_CHART: "Gráfico circular",
    WidgetType.TABLE: "Tabla",
}

# Tamaño inicial por tipo. Son valores de partida hasta que la FASE 5 defina el
# dimensionado real del grid.
DEFAULT_SIZE_BY_TYPE: dict[WidgetType, tuple[int, int]] = {
    WidgetType.KPI: (4, 3),
    WidgetType.BAR_CHART: (6, 4),
    WidgetType.LINE_CHART: (6, 4),
    WidgetType.PIE_CHART: (4, 4),
    WidgetType.TABLE: (12, 4),
}


class WidgetNotFoundError(Exception):
    """El widget no existe o no pertenece al usuario."""

    code = "WIDGET_NOT_FOUND"
    message = "Widget no encontrado."


class EmptyWidgetError(Exception):
    """Una actualización sin campos aplicables no se ejecuta."""

    code = "WIDGET_EMPTY_PATCH"
    message = "Indica al menos un campo para actualizar."


async def _require_widget(
    repository: WidgetRepository, widget_id: int, user_id: int
) -> Widget:
    widget = await repository.get_for_user(widget_id, user_id)
    if widget is None:
        raise WidgetNotFoundError(WidgetNotFoundError.message)
    return widget


async def list_widgets(session: AsyncSession, dashboard_id: int, user_id: int) -> Sequence[Widget]:
    # Se confirma la propiedad del dashboard antes de listar: listar los widgets de
    # un dashboard ajeno respondería 404, no una lista vacía.
    dashboard = await DashboardRepository(session).get_for_user(dashboard_id, user_id)
    if dashboard is None:
        raise WidgetNotFoundError(WidgetNotFoundError.message)
    return await WidgetRepository(session).list_for_dashboard(dashboard_id)


async def create_widget(
    session: AsyncSession, dashboard_id: int, user_id: int, payload: WidgetCreate
) -> Widget:
    repository = WidgetRepository(session)
    dashboard = await DashboardRepository(session).get_for_user(dashboard_id, user_id)
    if dashboard is None:
        raise WidgetNotFoundError(WidgetNotFoundError.message)

    if payload.layout is not None:
        x, y, width, height = payload.layout.x, payload.layout.y, payload.layout.w, payload.layout.h
    else:
        # Sin layout se apila debajo de lo que ya hay, para que dos widgets
        # seguidos no nazcan superpuestos.
        x, y = 0, await repository.next_free_row(dashboard_id)
        width, height = DEFAULT_SIZE_BY_TYPE[payload.type]

    widget = Widget(
        dashboard_id=dashboard_id,
        type=payload.type.value,
        title=payload.title or DEFAULT_TITLE_BY_TYPE[payload.type],
        configuration=payload.configuration.model_dump(exclude_none=True),
        x=x,
        y=y,
        w=width,
        h=height,
    )
    return await repository.add(widget)


async def update_widget(
    session: AsyncSession, widget_id: int, user_id: int, payload: WidgetUpdate
) -> Widget:
    repository = WidgetRepository(session)
    widget = await _require_widget(repository, widget_id, user_id)

    # exclude_unset distingue los campos omitidos de los enviados como null.
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise EmptyWidgetError(EmptyWidgetError.message)

    if "configuration" in changes:
        changes["configuration"] = payload.configuration.model_dump(exclude_none=True)
    if "layout" in changes:
        layout = changes.pop("layout")
        changes.update(x=layout["x"], y=layout["y"], w=layout["w"], h=layout["h"])

    for field, value in changes.items():
        setattr(widget, field, value)
    return await repository.update(widget)


async def delete_widget(session: AsyncSession, widget_id: int, user_id: int) -> None:
    repository = WidgetRepository(session)
    widget = await _require_widget(repository, widget_id, user_id)
    await repository.delete(widget)


async def update_dashboard_layouts(
    session: AsyncSession,
    dashboard_id: int,
    user_id: int,
    payload: DashboardLayoutUpdate,
) -> Sequence[Widget]:
    """Actualiza en lote las posiciones y tamaños del grid de un dashboard."""
    dashboard = await DashboardRepository(session).get_for_user(dashboard_id, user_id)
    if dashboard is None:
        raise WidgetNotFoundError(WidgetNotFoundError.message)

    repository = WidgetRepository(session)
    widgets = await repository.list_for_dashboard(dashboard_id)
    widgets_by_id = {widget.id: widget for widget in widgets}

    for item in payload.items:
        widget = widgets_by_id.get(item.id)
        if widget is None:
            raise WidgetNotFoundError(WidgetNotFoundError.message)
        widget.x = item.x
        widget.y = item.y
        widget.w = item.w
        widget.h = item.h

    await session.commit()
    for widget in widgets:
        await session.refresh(widget)
    return widgets
