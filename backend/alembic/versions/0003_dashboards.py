"""Tabla de dashboards. Cada dashboard pertenece a un usuario.

Revision ID: 0003_dashboards
Revises: 0002_users
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_dashboards"
down_revision: str | Sequence[str] | None = "0002_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dashboards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        # El borrado en cascada lo aplica la base de datos, no el ORM: así un
        # `delete()` en bloque de la suite de pruebas también limpia los dashboards.
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dashboards", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_dashboards_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("dashboards", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dashboards_user_id"))

    op.drop_table("dashboards")
