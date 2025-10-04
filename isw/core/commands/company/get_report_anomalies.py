from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.company_models import Company
from ...services.anomaly_detection import AnomalyDetectionConfig, XBRLAnomalyService
from ...services.database import DatabaseService
from ...services.vector_search import VectorSearchService


class GetReportAnomaliesCommand(ReadCommand):
    def __init__(self, cik: str, form_type: str, **kwargs):
        self.cik = cik
        self.form_type = form_type
        self.kwargs = kwargs
    
    def validate(self):
        if not self.cik:
            raise ValidationException("CIK is required")
        if not self.form_type:
            raise ValidationException("Form type is required")
        if self.form_type not in ['10-K', '10-Q']:
            raise ValidationException("Form type must be 10-K or 10-Q")
        return True
    
    def execute(self):
        config = AnomalyDetectionConfig()
        
        with DatabaseService.get_instance().session_scope() as session:
            # Get target company
            target_company = session.query(Company).filter(Company.cik == int(self.cik)).first()
            if not target_company:
                raise ValidationException(f"Company with CIK {self.cik} not found")
            
            if target_company.embedded_description is None:
                raise ValidationException("Target company has no embedding for similarity search")
            
            # Find similar peer companies
            filter_community = self.kwargs.get('filter_community', config.filter_community)
            community_filter = target_company.leiden_community if filter_community else None
            
            peer_results = VectorSearchService.find_similar_companies(
                session=session,
                query_embedding=target_company.embedded_description,
                similarity_threshold=self.kwargs.get('similarity_threshold', config.similarity_threshold),
                max_results=self.kwargs.get('n_peers', config.n_peers),
                community_filter=community_filter
            )
            
            peer_ciks = [company.cik for company, _ in peer_results if company.cik != int(self.cik)]
            
            if len(peer_ciks) < config.min_peers:
                raise ValidationException(
                    f"Insufficient similar peers found: {len(peer_ciks)} (need at least {config.min_peers})"
                )
            
            # Detect anomalies
            results = XBRLAnomalyService.detect_anomalies(
                session=session,
                target_cik=int(self.cik),
                peer_ciks=peer_ciks,
                form_type=self.form_type,
                fiscal_year=self.kwargs.get('fiscal_year'),
                filing_period=self.kwargs.get('filing_period'),
                common_threshold=self.kwargs.get('common_threshold', config.common_threshold),
                rare_threshold=self.kwargs.get('rare_threshold', config.rare_threshold),
                min_peers=config.min_peers
            )
            
            # Add peer information to summary
            results['summary']['peer_companies'] = [
                {
                    'cik': company.cik,
                    'company_name': company.company_name,
                    'similarity': float(similarity)
                }
                for company, similarity in peer_results if company.cik != int(self.cik)
            ]
            
            return results

