"""Rename companies table to entities with updated column names

Revision ID: 003
Revises: 002
Create Date: 2026-01-31 09:00:00.000000

This migration renames the companies table to entities and updates
the column name from company_name to name for cleaner terminology.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename companies table to entities."""
    # Rename table
    op.rename_table("companies", "entities")

    # Rename column company_name to name
    op.alter_column("entities", "company_name", new_column_name="name")

    # Update index names to reflect new table name
    op.drop_index("ix_companies_identifier", table_name="entities")
    op.drop_index("ix_companies_cluster", table_name="entities")
    op.drop_index("ix_companies_company_name", table_name="entities")
    op.drop_index("ix_companies_leiden_community", table_name="entities")

    op.create_index(op.f("ix_entities_identifier"), "entities", ["identifier"], unique=True)
    op.create_index(op.f("ix_entities_cluster"), "entities", ["cluster"], unique=False)
    op.create_index(op.f("ix_entities_name"), "entities", ["name"], unique=False)
    op.create_index(op.f("ix_entities_leiden_community"), "entities", ["leiden_community"], unique=False)


def downgrade() -> None:
    """Rename entities table back to companies."""
    # Drop new indexes
    op.drop_index(op.f("ix_entities_leiden_community"), table_name="entities")
    op.drop_index(op.f("ix_entities_name"), table_name="entities")
    op.drop_index(op.f("ix_entities_cluster"), table_name="entities")
    op.drop_index(op.f("ix_entities_identifier"), table_name="entities")

    # Rename column back
    op.alter_column("entities", "name", new_column_name="company_name")

    # Rename table back
    op.rename_table("entities", "companies")

    # Recreate old indexes
    op.create_index("ix_companies_identifier", "companies", ["identifier"], unique=True)
    op.create_index("ix_companies_cluster", "companies", ["cluster"], unique=False)
    op.create_index("ix_companies_company_name", "companies", ["company_name"], unique=False)
    op.create_index("ix_companies_leiden_community", "companies", ["leiden_community"], unique=False)
