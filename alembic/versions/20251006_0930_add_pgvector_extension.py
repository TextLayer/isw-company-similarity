"""add_pgvector_extension

Revision ID: bdb238e2d2ed
Revises: 
Create Date: 2025-10-06 09:30:51.060699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdb238e2d2ed'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Install pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
