from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, Integer, Numeric, String, Text
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
    sic = mapped_column(String(10), index=True)
    market_cap = mapped_column(Float)
    full_time_employees = mapped_column(Integer)
    
    # Clustering and community detection
    cluster = mapped_column(Integer, index=True)
    umap_x = mapped_column(Numeric(20, 10))
    umap_y = mapped_column(Numeric(20, 10))
    norm_mcap = mapped_column(Integer)
    norm_tot_rev = mapped_column(Integer)
    norm_fte = mapped_column(Integer)
    louvain_community = mapped_column(Integer, index=True)
    leiden_community = mapped_column(Integer, index=True)
    
    def __repr__(self):
        return f"<Company(cik={self.cik}, name='{self.company_name}', leiden_community={self.leiden_community})>"
    
    def to_dict(self):
        """Convert company to dictionary representation."""
        return {
            'id': self.id,
            'cik': self.cik,
            'company_name': self.company_name,
            'description': self.description,
            'sic': self.sic,
            'total_revenue': float(self.total_revenue) if self.total_revenue is not None else None,
            'market_cap': float(self.market_cap) if self.market_cap is not None else None,
            'full_time_employees': self.full_time_employees,
            'cluster': self.cluster,
            'norm_mcap': self.norm_mcap,
            'norm_tot_rev': self.norm_tot_rev,
            'norm_fte': self.norm_fte,
            'leiden_community': self.leiden_community,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }


class CompanyFacts(BaseModel):
    __tablename__ = "company_facts"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    cik = mapped_column(Integer, ForeignKey("companies.cik"), nullable=False, index=True)
    fact = mapped_column(Text, nullable=False, index=True)
    value = mapped_column(Text)
    fiscal_year = mapped_column(String(10), nullable=False, index=True)
    filing_period = mapped_column(String(10), nullable=False, index=True)
    form_type = mapped_column(String(10), nullable=False, index=True)

    def __repr__(self):
        return (
            f"<CompanyFacts(cik={self.cik}, fact={self.fact}, "
            f"fiscal_year={self.fiscal_year}, filing_period={self.filing_period})>"
        )

    def to_dict(self):
        return {
            'id': self.id,
            'cik': self.cik,
            'fact': self.fact,
            'value': self.value,
            'fiscal_year': self.fiscal_year,
            'filing_period': self.filing_period,
            'form_type': self.form_type,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }