"""Vector search service for company similarity operations."""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.company_models import Company


class VectorSearchService:
    """Core vector similarity search service using pgvector."""
    
    @staticmethod
    def find_similar_companies(
        session: Session,
        query_embedding: List[float],
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        sic_filter: Optional[str] = None,
        community_filter: Optional[int] = None
    ) -> List[Tuple[Company, float]]:
        """
        Core method: Find companies similar to a query embedding.
        
        Args:
            session: SQLAlchemy session
            query_embedding: Query vector embedding
            similarity_threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results to return
            sic_filter: Optional SIC code filter
            community_filter: Optional Leiden community ID to filter by
            
        Returns:
            List of tuples (company, similarity_score)
        """
        # Calculate cosine similarity: 1 - cosine_distance
        similarity_expr = 1 - Company.embedded_description.cosine_distance(query_embedding)
        
        query = select(
            Company,
            similarity_expr.label('similarity')
        ).where(
            similarity_expr > similarity_threshold
        )
        
        # Apply filters
        if sic_filter:
            query = query.where(Company.sic == sic_filter)
        
        if community_filter is not None:
            query = query.where(Company.leiden_community == community_filter)
        
        # Order by similarity and limit results
        query = query.order_by(similarity_expr.desc()).limit(max_results)
        
        results = session.execute(query).all()
        return [(row.Company, row.similarity) for row in results]


def create_hnsw_index(session: Session, m: int = 16, ef_construction: int = 64) -> None:
    """
    Create HNSW index for vector similarity search on embedded_description.
    
    Args:
        session: SQLAlchemy session
        m: Number of connections per layer
        ef_construction: Candidate list size during build
    """
    from sqlalchemy.schema import Index
    
    index = Index(
        'idx_companies_embedded_description_hnsw',
        Company.embedded_description,
        postgresql_using='hnsw',
        postgresql_with={'m': m, 'ef_construction': ef_construction},
        postgresql_ops={'embedded_description': 'vector_cosine_ops'}
    )
    
    index.create(session.bind)


def create_ivfflat_index(session: Session, lists: int = 100) -> None:
    """
    Create IVFFlat index for vector similarity search on embedded_description.
    
    Args:
        session: SQLAlchemy session
        lists: Number of clusters
    """
    from sqlalchemy.schema import Index
    
    index = Index(
        'idx_companies_embedded_description_ivfflat',
        Company.embedded_description,
        postgresql_using='ivfflat',
        postgresql_with={'lists': lists},
        postgresql_ops={'embedded_description': 'vector_cosine_ops'}
    )
    
    index.create(session.bind)

