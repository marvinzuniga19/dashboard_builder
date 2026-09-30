"""Widget de un dashboard: una pieza visual con tipo, configuración y posición.

``type`` se guarda como texto y se valida contra :class:`WidgetType` en Python, sin
``CHECK`` en la base: AGENTS.md pide poder añadir tipos nuevos después, y una
restricción en la tabla obligaría a una migración cada vez que aparezca uno.

El layout vive en cuatro columnas y no en un JSON porque la FASE 5 lo actualiza
en cada fin de arrastre y así se puede ordenar y filtrar en SQL. La API expone
estas mismas cuatro cifras como un objeto ``layout`` para ser compatible con
react-grid-layout.
"""

import datetime as dt
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

MAXIMUM_TITLE_LENGTH = 120
TYPE_LENGTH = 32

# Límites del grid. react-grid-layout trabaja con 12 columnas; se acotan también
# las filas para que una petición no pueda empujar el lienzo a alturas absurdas.
GRID_COLUMNS = 12
MAXIMUM_ROWS = 24


class WidgetType(StrEnum):
    KPI = "KPI"
    BAR_CHART = "BAR_CHART"
    LINE_CHART = "LINE_CHART"
    PIE_CHART = "PIE_CHART"
    TABLE = "TABLE"


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(
        ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(TYPE_LENGTH), nullable=False)
    title: Mapped[str] = mapped_column(String(MAXIMUM_TITLE_LENGTH), nullable=False)
    # `configuration` se sustituye siempre por un dict nuevo, nunca se muta en
    # sitio: por eso no hace falta `MutableDict` para que el cambio se persista.
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    x: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    y: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    w: Mapped[int] = mapped_column(Integer, nullable=False, default=GRID_COLUMNS)
    h: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"Widget(id={self.id!r}, type={self.type!r}, dashboard_id={self.dashboard_id!r})"
