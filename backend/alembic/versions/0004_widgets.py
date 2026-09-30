"""Tabla de widgets. Cada widget pertenece a un dashboard y, por cascada, al
usuario propietario de ese dashboard.

Revision ID: 0004_widgets
Revises: 0003_dashboards
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_widgets"
down_revision: str | Sequence[str] | None = "0003_dashboards"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "widgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dashboard_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("w", sa.Integer(), nullable=False),
        sa.Column("h", sa.Integer(), nullable=False),
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
        # Cascada en cascada: al borrar el dashboard desaparecen sus widgets sin
        # pasar por el ORM, igual que sus dashboards al borrar el usuario.
        sa.ForeignKeyConstraint(["dashboard_id"], ["dashboards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("widgets", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_widgets_dashboard_id"), ["dashboard_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("widgets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_widgets_dashboard_id"))

    op.drop_table("widgets")
