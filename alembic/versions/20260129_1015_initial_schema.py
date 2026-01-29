"""Initial schema with pgvector and companies table

Revision ID: 001
Revises:
Create Date: 2026-01-29 10:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pgvector extension and companies table."""
    # Install pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cik", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedded_description", Vector(1536), nullable=True),
        sa.Column("total_revenue", sa.Float(), nullable=True),
        sa.Column("norm_tot_rev", sa.Integer(), nullable=True),
        sa.Column("cluster", sa.Integer(), nullable=True),
        sa.Column("leiden_community", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_cik"), "companies", ["cik"], unique=True)
    op.create_index(op.f("ix_companies_cluster"), "companies", ["cluster"], unique=False)
    op.create_index(op.f("ix_companies_company_name"), "companies", ["company_name"], unique=False)
    op.create_index(op.f("ix_companies_leiden_community"), "companies", ["leiden_community"], unique=False)


def downgrade() -> None:
    """Drop companies table and pgvector extension."""
    op.drop_index(op.f("ix_companies_leiden_community"), table_name="companies")
    op.drop_index(op.f("ix_companies_company_name"), table_name="companies")
    op.drop_index(op.f("ix_companies_cluster"), table_name="companies")
    op.drop_index(op.f("ix_companies_cik"), table_name="companies")
    op.drop_table("companies")
    op.execute("DROP EXTENSION IF EXISTS vector")
