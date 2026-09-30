"""Acceso a la tabla de widgets. No contiene reglas de negocio.

Un widget no tiene ``user_id``: su propietario se alcanza por el dashboard al que
pertenece, así que toda consulta que.lo localice por identificador une las dos
tablas y filtra por el usuario. Filtrar solo por ``widgets.id`` devolvería
widgets de otra cuenta.
"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard import Dashboard
from app.models.widget import Widget


class WidgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_dashboard(self, dashboard_id: int) -> Sequence[Widget]:
        # Orden de inserción, con desempate por id: `created_at` tiene precisión
        # de segundo en SQLite.
        result = await self._session.execute(
            select(Widget)
            .where(Widget.dashboard_id == dashboard_id)
            .order_by(Widget.created_at, Widget.id)
        )
        return result.scalars().all()

    async def get_for_user(self, widget_id: int, user_id: int) -> Widget | None:
        result = await self._session.execute(
            self._owned_query().where(Widget.id == widget_id, Dashboard.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add(self, widget: Widget) -> Widget:
        self._session.add(widget)
        await self._session.commit()
        await self._session.refresh(widget)
        return widget

    async def update(self, widget: Widget) -> Widget:
        await self._session.commit()
        await self._session.refresh(widget)
        return widget

    async def delete(self, widget: Widget) -> None:
        await self._session.delete(widget)
        await self._session.commit()

    async def next_free_row(self, dashboard_id: int) -> int:
        """Fila libre más baja del dashboard, para apilar widgets sin solaparse."""
        result = await self._session.execute(
            select(func.coalesce(func.max(Widget.y + Widget.h), 0)).where(
                Widget.dashboard_id == dashboard_id
            )
        )
        return result.scalar_one() or 0

    @staticmethod
    def _owned_query() -> select:
        return select(Widget).join(Dashboard, Widget.dashboard_id == Dashboard.id)
