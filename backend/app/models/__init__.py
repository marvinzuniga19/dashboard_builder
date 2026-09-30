"""Importar aquí los modelos de futuras fases para que Alembic los detecte."""

from app.models.dashboard import Dashboard
from app.models.user import User
from app.models.widget import Widget, WidgetType

__all__ = ["Dashboard", "User", "Widget", "WidgetType"]
