from datetime import datetime

from ....shared.config import with_config
from ...schemas.recruitment_schemas import CandidateDetailsData, candidate_details_schema
from ...services.llm.embedding import EmbeddingClient
from ...services.search.service import SearchService
from ..base import WriteCommand


class CreateCandidateCommand(WriteCommand):
    """Create a search candidate document"""

    def __init__(
        self,
        application_id: str,
        candidate_id: str,
        current_interview_stage: str,
        full_name: str,
        job_id: str,
        recommendation: str,
        resume_text: str,
    ):
        self.application_id = application_id
        self.candidate_id = candidate_id
        self.job_id = job_id
        self.current_interview_stage = current_interview_stage
        self.created_at = datetime.now().isoformat()
        self.full_name = full_name
        self.recommendation = recommendation
        self.resume_text = resume_text
        self.updated_at = datetime.now().isoformat()

    @with_config("recruitment_candidate_index")
    def execute(self, recruitment_candidate_index: str) -> CandidateDetailsData:
        """
        Create a candidate in the candidate index with resume text embedding

        Args:
            recruitment_candidate_index (str): The name of the candidate index

        Returns:
            CandidateDetailsData: The candidate details
        """
        result = SearchService("opensearch").create_document(
            index=recruitment_candidate_index,
            document={
                **self.__dict__,
                "embedding": EmbeddingClient().embed(self.resume_text),
            },
            document_id=self.candidate_id,
        )

        return candidate_details_schema.load(
            {
                **result.get("_source"),
                "id": result.get("_id"),
            },
            partial=True,
        )

    def validate(self):
        """Validate the candidate input details"""
        candidate_details_schema.load(self.__dict__)
