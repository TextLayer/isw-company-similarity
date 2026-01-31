"""Add revenue currency fields

Revision ID: 004
Revises: 003
Create Date: 2026-01-31 14:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename total_revenue to revenue_raw for clarity
    op.alter_column("entities", "total_revenue", new_column_name="revenue_raw")

    # Add new revenue columns
    op.add_column("entities", sa.Column("revenue_currency", sa.String(10), nullable=True))
    op.add_column("entities", sa.Column("revenue_usd", sa.Float(), nullable=True))
    op.add_column("entities", sa.Column("revenue_period_end", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("entities", "revenue_period_end")
    op.drop_column("entities", "revenue_usd")
    op.drop_column("entities", "revenue_currency")
    op.alter_column("entities", "revenue_raw", new_column_name="total_revenue")
