from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.company_models import Company
from ...services.database.service import DatabaseService
from ...services.vector_search import VectorSearchService


class GetSimilarCompaniesCommand(ReadCommand):
    def __init__(
        self, cik: str, similarity_threshold: float = 0.7, max_results: int = 10, filter_community: bool = True
    ):
        self.cik = cik
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.filter_community = filter_community

    def validate(self) -> bool:
        if not self.cik:
            raise ValidationException("CIK is required")

        return True

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            company = session.query(Company).filter(Company.cik == self.cik).first()
            if not company:
                raise ValidationException("Company not found")

            # Determine community filter
            community_filter = company.leiden_community if self.filter_community else None

            # Get similar companies
            results = VectorSearchService.find_similar_companies(
                session=session,
                query_embedding=company.embedded_description,
                similarity_threshold=self.similarity_threshold,
                max_results=self.max_results,
                community_filter=community_filter,
            )

            # Serialize results
            return [
                {"company": similar_company.to_dict(), "similarity": float(similarity)}
                for similar_company, similarity in results
                if similar_company.cik != company.cik
            ]
