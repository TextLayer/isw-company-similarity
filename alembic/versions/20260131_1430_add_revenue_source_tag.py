"""Add revenue source tags field

Revision ID: 005
Revises: 004
Create Date: 2026-01-31 14:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("entities", sa.Column("revenue_source_tags", ARRAY(sa.String(100)), nullable=True))


def downgrade() -> None:
    op.drop_column("entities", "revenue_source_tags")
