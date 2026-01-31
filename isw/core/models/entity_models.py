from typing import Literal

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session, mapped_column
from sqlalchemy.schema import Index

from isw.core.models.base import BaseModel
from isw.core.services.entities import IdentifierType, Jurisdiction


class Entity(BaseModel):
    """Entity model with vector embeddings for similarity search.

    Represents a legal entity that files with regulatory bodies.
    Supports entities from multiple jurisdictions:
    - US: identified by CIK (SEC Central Index Key)
    - EU/UK: identified by LEI (Legal Entity Identifier)
    """

    __tablename__ = "entities"

    # Primary key
    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Entity identification (supports CIK for US, LEI for EU/UK)
    identifier = mapped_column(String(20), nullable=False, unique=True, index=True)
    identifier_type = mapped_column(String(10), nullable=False)  # "CIK" or "LEI"
    jurisdiction = mapped_column(String(10), nullable=False)  # "US", "EU", "UK"

    # Basic entity information
    name = mapped_column(String(500), nullable=False, index=True)
    description = mapped_column(Text)

    # Vector embedding for similarity search (1536 dimensions for OpenAI embeddings)
    embedded_description = mapped_column(Vector(1536))

    # Revenue data
    revenue_raw = mapped_column(Float)  # Original amount in source currency
    revenue_currency = mapped_column(String(10))  # Source currency code (USD, EUR, GBP, etc.)
    revenue_usd = mapped_column(Float)  # Converted to USD for comparison
    revenue_period_end = mapped_column(String(20))  # Period end date of revenue data
    revenue_source_tags = mapped_column(ARRAY(String(100)))  # XBRL tags used to extract revenue
    norm_tot_rev = mapped_column(Integer)  # Normalized bucket for similarity

    # Clustering and community detection
    cluster = mapped_column(Integer, index=True)
    leiden_community = mapped_column(Integer, index=True)

    # -------------------------------------------------------------------------
    # Vector index operations (schema-level)
    # -------------------------------------------------------------------------

    @classmethod
    def create_vector_index(
        cls,
        session: Session,
        index_type: Literal["hnsw", "ivfflat"] = "hnsw",
        **kwargs,
    ) -> None:
        """
        Create a pgvector index on the embedded_description column.

        Args:
            session: SQLAlchemy session
            index_type: "hnsw" (faster queries) or "ivfflat" (faster builds)
            **kwargs: Index-specific options
                - hnsw: m (default 16), ef_construction (default 64)
                - ivfflat: lists (default 100)
        """
        if index_type == "hnsw":
            m = kwargs.get("m", 16)
            ef_construction = kwargs.get("ef_construction", 64)
            index = Index(
                f"idx_{cls.__tablename__}_embedding_hnsw",
                cls.embedded_description,
                postgresql_using="hnsw",
                postgresql_with={"m": m, "ef_construction": ef_construction},
                postgresql_ops={"embedded_description": "vector_cosine_ops"},
            )
        elif index_type == "ivfflat":
            lists = kwargs.get("lists", 100)
            index = Index(
                f"idx_{cls.__tablename__}_embedding_ivfflat",
                cls.embedded_description,
                postgresql_using="ivfflat",
                postgresql_with={"lists": lists},
                postgresql_ops={"embedded_description": "vector_cosine_ops"},
            )
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        index.create(session.bind)

    # -------------------------------------------------------------------------
    # Standard model methods
    # -------------------------------------------------------------------------

    def __repr__(self):
        return f"<Entity(identifier={self.identifier}, type={self.identifier_type}, name='{self.name}')>"

    def to_dict(self):
        """Convert entity to dictionary representation."""
        return {
            "id": self.id,
            "identifier": self.identifier,
            "identifier_type": self.identifier_type,
            "jurisdiction": self.jurisdiction,
            "name": self.name,
            "description": self.description,
            "revenue_raw": float(self.revenue_raw) if self.revenue_raw is not None else None,
            "revenue_currency": self.revenue_currency,
            "revenue_usd": float(self.revenue_usd) if self.revenue_usd is not None else None,
            "revenue_period_end": self.revenue_period_end,
            "revenue_source_tags": self.revenue_source_tags,
            "norm_tot_rev": self.norm_tot_rev,
            "cluster": self.cluster,
            "leiden_community": self.leiden_community,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }

    @classmethod
    def from_entity_record(cls, record) -> "Entity":
        """Create an Entity from an EntityRecord.

        Args:
            record: EntityRecord from entity registry.

        Returns:
            Entity instance (not yet persisted).
        """
        return cls(
            identifier=record.identifier,
            identifier_type=record.identifier_type.value,
            jurisdiction=record.jurisdiction.value,
            name=record.name,
        )

    def get_identifier_type_enum(self) -> IdentifierType:
        """Get identifier type as enum."""
        return IdentifierType(self.identifier_type)

    def get_jurisdiction_enum(self) -> Jurisdiction:
        """Get jurisdiction as enum."""
        return Jurisdiction(self.jurisdiction)
