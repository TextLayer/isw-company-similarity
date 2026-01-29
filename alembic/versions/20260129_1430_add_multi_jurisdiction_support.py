"""Add multi-jurisdiction support with identifier/identifier_type/jurisdiction

Revision ID: 002
Revises: 001
Create Date: 2026-01-29 14:30:00.000000

This migration updates the companies table to support entities from
multiple jurisdictions (US, EU, UK) with different identifier types
(CIK for US, LEI for EU/UK).

Changes:
- Replace `cik` (Integer) with `identifier` (String)
- Add `identifier_type` column (CIK or LEI)
- Add `jurisdiction` column (US, EU, UK)
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add multi-jurisdiction identifier support."""
    # Add new columns
    op.add_column(
        "companies",
        sa.Column("identifier", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("identifier_type", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("jurisdiction", sa.String(length=10), nullable=True),
    )

    # Migrate existing CIK data to new identifier column
    # CIK is zero-padded to 10 digits
    op.execute(
        """
        UPDATE companies
        SET identifier = LPAD(cik::text, 10, '0'),
            identifier_type = 'CIK',
            jurisdiction = 'US'
        WHERE cik IS NOT NULL
        """
    )

    # Make new columns non-nullable after data migration
    op.alter_column("companies", "identifier", nullable=False)
    op.alter_column("companies", "identifier_type", nullable=False)
    op.alter_column("companies", "jurisdiction", nullable=False)

    # Drop old CIK index and column
    op.drop_index("ix_companies_cik", table_name="companies")
    op.drop_column("companies", "cik")

    # Create new index on identifier
    op.create_index(op.f("ix_companies_identifier"), "companies", ["identifier"], unique=True)


def downgrade() -> None:
    """Revert to CIK-only schema.

    WARNING: This downgrade DELETES all EU/UK entities (non-CIK records)
    since they cannot be represented in the old schema. This is intentional
    as there is no way to store LEI identifiers in an Integer column.

    If EU/UK entities have relationships (embeddings, clusters, etc.),
    those will be orphaned. Consider backing up data before downgrading.
    """
    # Add back cik column
    op.add_column(
        "companies",
        sa.Column("cik", sa.Integer(), nullable=True),
    )

    # Migrate identifier back to cik (only for CIK type)
    op.execute(
        """
        UPDATE companies
        SET cik = identifier::integer
        WHERE identifier_type = 'CIK'
        """
    )

    # Delete non-CIK records (they can't be represented in old schema)
    # This is intentional - LEI identifiers cannot fit in an Integer column
    op.execute(
        """
        DELETE FROM companies
        WHERE identifier_type != 'CIK'
        """
    )

    # Make cik non-nullable
    op.alter_column("companies", "cik", nullable=False)

    # Drop new columns and indexes
    op.drop_index(op.f("ix_companies_identifier"), table_name="companies")
    op.drop_column("companies", "jurisdiction")
    op.drop_column("companies", "identifier_type")
    op.drop_column("companies", "identifier")

    # Recreate old index
    op.create_index("ix_companies_cik", "companies", ["cik"], unique=True)
