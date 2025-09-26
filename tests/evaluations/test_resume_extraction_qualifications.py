from tests.evaluations.base import FunctionalEvaluator
from tests.fixtures import load_fixture_json
from isw.core.commands.recruitment.analyze_candidate_resume import AnalyzeCandidateResumeCommand


class TestResumeExtractionQualifications(FunctionalEvaluator):
    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_rick_sanchez_qualifications(self):
        self.judge(
            llm_output=self._get_qualifications_for_candidate("rick_sanchez"),
            llm_output_expected="""
            - NLP CS framework
            - Senior AI engineer
            - Python expertise
            - User-to-agent interactions
            - OT2 Search at OpenText
            - OpenAI API
            - ML data pipelines
            - PDF document processing
            - AWS, Azure and GCP cloud
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_homer_simpson_qualifications(self):
        self.judge(
            llm_output=self._get_qualifications_for_candidate("homer_simpson"),
            llm_output_expected="""
            - NLP-based Q&A system
            - AI and machine learning engineer
            - Python proficiency
            - RAG pipeline to knowledge base
            - Architected LLMOps Framework
            - OpenAI
            - HuggingFace
            - Docker
            - PyTorch
            - LLM and vector-database fine-tuning
            - Traceability
            - Large-scale data engineering pipelines
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_bob_belcher_qualifications(self):
        self.judge(
            llm_output=self._get_qualifications_for_candidate("bob_belcher"),
            llm_output_expected="""
            - **Misalignments include RAG systems, OpenAI, HuggingFace, vector databases**
            - NLP techniques (PCA, tokenization, LSTM)
            - Production-level Python
            - PyTorch
            - CI/CD pipelines
            - AWS SageMaker and Azure ML
            - LLM fine-tuning with private datasets, policy documents, metadata
            """,
            judge="summary",
        )

    def _get_qualifications_for_candidate(self, candidate_name: str) -> str:
        return AnalyzeCandidateResumeCommand(
            job_spec=load_fixture_json("jobs/ai_engineer"),
        ).execute_extraction_of_qualifications(
            resume_formatted=load_fixture_json(f"candidates/parsed/{candidate_name}"),
        )
