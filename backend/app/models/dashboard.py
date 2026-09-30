"""Dashboard de un usuario. Los widgets se añaden en la FASE 4.

Las longitudes de las columnas viven aquí porque son el límite real del
almacenamiento; ``app/schemas/dashboard.py`` las reutiliza para validar la entrada
y evitar que ambas se desincronicen.

No se declaran relaciones ORM: la pertenencia al usuario se resuelve filtrando
por ``user_id`` y el borrado en cascada lo aplica la base de datos con
``ondelete="CASCADE"``, de modo que no depende del modelo para no dejar filas
huérfanas.
"""

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

MAXIMUM_NAME_LENGTH = 120
MAXIMUM_DESCRIPTION_LENGTH = 1000


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(MAXIMUM_NAME_LENGTH), nullable=False)
    description: Mapped[str | None] = mapped_column(String(MAXIMUM_DESCRIPTION_LENGTH))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"Dashboard(id={self.id!r}, name={self.name!r}, user_id={self.user_id!r})"
