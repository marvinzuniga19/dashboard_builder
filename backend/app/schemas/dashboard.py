"""Contratos HTTP de dashboards.

La normalización (quitar espacios y convertir una descripción vacía en ``None``)
se aplica en modo ``before``, antes de validar longitudes: así un nombre formado
solo por espacios se rechaza como violation de longitud mínima en lugar de
llegar al servicio y almacenarse tal cual.
"""

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.dashboard import MAXIMUM_DESCRIPTION_LENGTH, MAXIMUM_NAME_LENGTH

# Techos del listado. Acotan el coste de la consulta; 100 filas bastan para
# llenar cualquier pantalla de la aplicación de una sola vez.
DEFAULT_PAGE_SIZE = 20
MAXIMUM_PAGE_SIZE = 100


class DashboardCreate(BaseModel):
    # `extra="forbid"` es deliberado: Pydantic ignora lo desconocido por defecto, y
    # eso convierte un campo mal escrito ("nombre" en vez de "name") en un no-op
    # invisible. También hace explícito que `user_id` no se acepta en el cuerpo:
    # el propietario lo impone la sesión, nunca el cliente.
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=MAXIMUM_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAXIMUM_DESCRIPTION_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        return value.strip() or None


class DashboardUpdate(BaseModel):
    """Actualización parcial: solo se aplican los campos presentes en el payload.

    Los validadores ``before`` no se ejecutan sobre los valores por defecto, de
    modo que omitir ``description`` no la borra: el servicio usa
    ``exclude_unset`` para distinguir "no enviado" de "enviado como null".
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=MAXIMUM_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAXIMUM_DESCRIPTION_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def reject_null_name(cls, value: Any) -> Any:
        # A diferencia de Create, aquí null llega como actualización explícita y
        # la columna es NOT NULL: el error debe ser de validación, no un 500.
        if value is None:
            raise ValueError("El nombre no puede ser nulo.")
        return value.strip() if isinstance(value, str) else value

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        return value.strip() or None


class DashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime


class DashboardPage(BaseModel):
    """Envelope del listado.

    ``total`` es necesario: sin él el frontend no sabe si hay páginas
    siguientes ni cuántas filas hay en total.
    """

    items: list[DashboardRead]
    total: int
    limit: int
    offset: int
