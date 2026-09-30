"""Acceso a la tabla de dashboards. No contiene reglas de negocio.

Todas las consultas reciben ``user_id``: el aislamiento entre usuarios se aplica
en la consulta, no filtrando después en Python.
"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard import Dashboard


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self, user_id: int, limit: int, offset: int
    ) -> tuple[Sequence[Dashboard], int]:
        filters = Dashboard.user_id == user_id
        # El desempate por id es obligatorio: `updated_at` tiene precisión de
        # segundo en SQLite, así que sin él una página podría repetir o saltar
        # elementos al recorrer el listado.
        ordering = (Dashboard.updated_at.desc(), Dashboard.id.desc())
        result = await self._session.execute(
            select(Dashboard).where(filters).order_by(*ordering).limit(limit).offset(offset)
        )
        total = await self._session.scalar(
            select(func.count()).select_from(Dashboard).where(filters)
        )
        return result.scalars().all(), total or 0

    async def get_for_user(self, dashboard_id: int, user_id: int) -> Dashboard | None:
        result = await self._session.execute(
            select(Dashboard).where(
                Dashboard.id == dashboard_id, Dashboard.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def add(self, dashboard: Dashboard) -> Dashboard:
        self._session.add(dashboard)
        await self._session.commit()
        await self._session.refresh(dashboard)
        return dashboard

    async def update(self, dashboard: Dashboard) -> Dashboard:
        await self._session.commit()
        await self._session.refresh(dashboard)
        return dashboard

    async def delete(self, dashboard: Dashboard) -> None:
        await self._session.delete(dashboard)
        await self._session.commit()
