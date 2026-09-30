"""Contratos HTTP de widgets.

``configuration`` se valida con un modelo propio en lugar de aceptar un JSON
libre: en esta fase solo existe la forma documentada en AGENTS.md
(``dataset``, ``dimension``, ``metric``, ``aggregation``), y aceptarla a pelo
permitiría guardar basura que la FASE 8 tendría que sanear. Se amplía en la FASE
9 sin romper lo ya guardado.
"""

import datetime as dt
from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.models.widget import (
    GRID_COLUMNS,
    MAXIMUM_ROWS,
    MAXIMUM_TITLE_LENGTH,
    WidgetType,
)

MAXIMUM_FIELD_NAME_LENGTH = 120


class Aggregation(StrEnum):
    """Agregaciones admitidas. La FASE 8 será la que las consolide."""

    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    DISTINCT_COUNT = "distinct_count"


class WidgetConfiguration(BaseModel):
    """Consulta descrita de forma estructurada. Todo es opcional por ahora.

    No se acepta SQL ni texto libre: el backend convierte esta estructura en
    consultas seguras cuando exista el query engine (AGENTS.md, seguridad de
    consultas).
    """

    model_config = ConfigDict(extra="forbid")

    dataset: str | None = Field(default=None, min_length=1, max_length=MAXIMUM_FIELD_NAME_LENGTH)
    dimension: str | None = Field(default=None, min_length=1, max_length=MAXIMUM_FIELD_NAME_LENGTH)
    metric: str | None = Field(default=None, min_length=1, max_length=MAXIMUM_FIELD_NAME_LENGTH)
    aggregation: Aggregation | None = None

    @field_validator("dataset", "dimension", "metric", mode="before")
    @classmethod
    def strip_field_name(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        # Una cadena solo con espacios se convierte en None en lugar de fallar
        # por longitud mínima: "no informado" es el estado normal de un widget
        # recién creado.
        return value.strip() or None


class Layout(BaseModel):
    """Posición y tamaño, en las unidades de react-grid-layout.

    Las cuatro cifras son obligatorias y no tienen valores por defecto: en un
    ``PATCH`` enviar solo ``w`` no debe reubicar el widget en (0, 0) con una
    altura inventada, sino ser un error de validación. Si no se envía layout al
    crear, el servicio coloca el widget automáticamente.
    """

    model_config = ConfigDict(extra="forbid")

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=1, le=GRID_COLUMNS)
    h: int = Field(ge=1, le=MAXIMUM_ROWS)


class WidgetCreate(BaseModel):
    # `extra="forbid"` por el mismo motivo que en dashboards: un campo mal
    # escrito no debe convertirse en un no-op silencioso. También impide mover un
    # widget a otro dashboard desde el cuerpo de la petición.
    model_config = ConfigDict(extra="forbid")

    type: WidgetType
    title: str | None = Field(default=None, min_length=1, max_length=MAXIMUM_TITLE_LENGTH)
    configuration: WidgetConfiguration = Field(default_factory=WidgetConfiguration)
    layout: Layout | None = None

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: Any) -> Any:
        # Vacío o solo espacios no es un título: se deja en None y el servicio
        # aplica el nombre por defecto del tipo.
        return value.strip() or None if isinstance(value, str) else value


class WidgetUpdate(BaseModel):
    """Actualización parcial. ``type`` y el dashboard no son modificables.

    Cambiar el tipo invalidaría la configuración guardada, así que se rechaza en
    vez de aceptarse en silencio; la FASE 9 resuelve el cambio sustituyendo el
    widget.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=MAXIMUM_TITLE_LENGTH)
    configuration: WidgetConfiguration | None = None
    layout: Layout | None = None

    @field_validator("title", mode="before")
    @classmethod
    def reject_blank_title(cls, value: Any) -> Any:
        # Aquí null sí es un error, a diferencia de la creación: la columna es
        # NOT NULL y no hay un nombre por defecto que aplicar a un PATCH.
        if value is None:
            raise ValueError("El título no puede ser nulo.")
        if isinstance(value, str) and not value.strip():
            raise ValueError("El título no puede estar vacío.")
        return value.strip() if isinstance(value, str) else value

    @field_validator("configuration", "layout", mode="before")
    @classmethod
    def reject_null_object(cls, value: Any, info: ValidationInfo) -> Any:
        # Un objeto omitido no se toca; uno enviado a null no significa nada y el
        # servicio no puede aplicarlo. Se rechaza aquí y no en el servicio para
        # que sea un 422 como el resto de entradas inválidas, y no un 500.
        # Para vaciar la configuración se envía `{}`, que sí es un objeto válido.
        if value is None:
            raise ValueError(
                f"«{info.field_name}» no puede ser nulo; omite el campo para no modificarlo."
            )
        return value


class WidgetLayoutItem(Layout):
    """Posición y tamaño asignados a un widget específico en el grid."""

    id: int = Field(ge=1)


class DashboardLayoutUpdate(BaseModel):
    """Lote de posiciones para actualizar el lienzo completo de un dashboard."""

    model_config = ConfigDict(extra="forbid")

    items: list[WidgetLayoutItem]

    @field_validator("items")
    @classmethod
    def reject_duplicate_ids(cls, items: list[WidgetLayoutItem]) -> list[WidgetLayoutItem]:
        seen: set[int] = set()
        for item in items:
            if item.id in seen:
                raise ValueError(f"El identificador {item.id} está duplicado en el lote.")
            seen.add(item.id)
        return items


class WidgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dashboard_id: int
    type: WidgetType
    title: str
    configuration: WidgetConfiguration
    layout: Layout
    created_at: dt.datetime
    updated_at: dt.datetime

    @model_validator(mode="before")
    @classmethod
    def group_layout(cls, data: Any) -> Any:
        """Ensambla ``layout`` a partir de las cuatro columnas planas del modelo."""
        if not hasattr(data, "x"):
            return data
        return {
            "id": data.id,
            "dashboard_id": data.dashboard_id,
            "type": data.type,
            "title": data.title,
            "configuration": data.configuration,
            "layout": {"x": data.x, "y": data.y, "w": data.w, "h": data.h},
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }
