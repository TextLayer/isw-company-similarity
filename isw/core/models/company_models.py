from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import mapped_column

from isw.core.models.base import BaseModel
from isw.core.services.entity_collection.base import IdentifierType, Jurisdiction


class Company(BaseModel):
    """Company model with vector embeddings for similarity search.

    Supports entities from multiple jurisdictions:
    - US: identified by CIK (SEC Central Index Key)
    - EU/UK: identified by LEI (Legal Entity Identifier)
    """

    __tablename__ = "companies"

    # Primary key
    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Entity identification (supports CIK for US, LEI for EU/UK)
    identifier = mapped_column(String(20), nullable=False, unique=True, index=True)
    identifier_type = mapped_column(String(10), nullable=False)  # "CIK" or "LEI"
    jurisdiction = mapped_column(String(10), nullable=False)  # "US", "EU", "UK"

    # Basic company information
    company_name = mapped_column(String(500), nullable=False, index=True)
    description = mapped_column(Text)

    # Vector embedding for similarity search (1536 dimensions for OpenAI embeddings)
    embedded_description = mapped_column(Vector(1536))

    # Company metrics
    total_revenue = mapped_column(Float)
    norm_tot_rev = mapped_column(Integer)

    # Clustering and community detection
    cluster = mapped_column(Integer, index=True)
    leiden_community = mapped_column(Integer, index=True)

    def __repr__(self):
        return f"<Company(identifier={self.identifier}, type={self.identifier_type}, name='{self.company_name}')>"

    def to_dict(self):
        """Convert company to dictionary representation."""
        return {
            "id": self.id,
            "identifier": self.identifier,
            "identifier_type": self.identifier_type,
            "jurisdiction": self.jurisdiction,
            "company_name": self.company_name,
            "description": self.description,
            "total_revenue": (float(self.total_revenue) if self.total_revenue is not None else None),
            "norm_tot_rev": self.norm_tot_rev,
            "cluster": self.cluster,
            "leiden_community": self.leiden_community,
            "created_at": (self.created_at.isoformat() if self.created_at is not None else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at is not None else None),
        }

    @classmethod
    def from_entity_record(cls, record) -> "Company":
        """Create a Company from an EntityRecord.

        Args:
            record: EntityRecord from entity collection.

        Returns:
            Company instance (not yet persisted).
        """
        return cls(
            identifier=record.identifier,
            identifier_type=record.identifier_type.value,
            jurisdiction=record.jurisdiction.value,
            company_name=record.name,
        )

    def get_identifier_type_enum(self) -> IdentifierType:
        """Get identifier type as enum."""
        return IdentifierType(self.identifier_type)

    def get_jurisdiction_enum(self) -> Jurisdiction:
        """Get jurisdiction as enum."""
        return Jurisdiction(self.jurisdiction)
