from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import mapped_column

from isw.core.models.base import BaseModel


class Company(BaseModel):
    """Company model with vector embeddings for similarity search."""

    __tablename__ = "companies"

    # Primary key
    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    # CIK identifier
    cik = mapped_column(Integer, nullable=False, unique=True, index=True)

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
        return f"<Company(cik={self.cik}, name='{self.company_name}', leiden_community={self.leiden_community})>"

    def to_dict(self):
        """Convert company to dictionary representation."""
        return {
            "id": self.id,
            "cik": self.cik,
            "company_name": self.company_name,
            "description": self.description,
            "total_revenue": float(self.total_revenue) if self.total_revenue is not None else None,
            "norm_tot_rev": self.norm_tot_rev,
            "cluster": self.cluster,
            "leiden_community": self.leiden_community,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }
