from isw.core.commands.recruitment.analyze_candidate_resume import AnalyzeCandidateResumeCommand
from tests.evaluations.base import FunctionalEvaluator
from tests.fixtures import load_fixture_json


class TestResumeExtractionFlags(FunctionalEvaluator):
    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_rick_sanchez_flags(self):
        self.judge(
            llm_output=self._get_flags_for_candidate("rick_sanchez"),
            llm_output_expected="""
            * Highlighted in green flags notes:*
            - Experience with NLP frameworks and ML pipelines
            - Experience with document processing
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_sterling_archer_flags(self):
        self.judge(
            llm_output=self._get_flags_for_candidate("sterling_archer"),
            llm_output_expected="""
            * Highlighed in green flags notes:*
            - Experience with vectorized search
            - Experience with agentic systems
            - Experience with ML pipelines
            - Tensorflow and PyTorch
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_bob_belcher_flags(self):
        self.judge(
            llm_output=self._get_flags_for_candidate("bob_belcher"),
            llm_output_expected="""
            * Highlighed in green flags notes:*
            - NLP
            - ML or MLOps (Dataiku and Azure)
            - PyTorch
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_homer_simpson_flags(self):
        self.judge(
            llm_output=self._get_flags_for_candidate("homer_simpson"),
            llm_output_expected="""
            * Highlighed in green flags notes:*
            - Published on NLP classification
            - Demonstrated RAG skills (with OpenAI, Weaviate, LangSmith, Gemini)
            """,
            judge="summary",
        )

    def _get_flags_for_candidate(self, candidate_name: str) -> str:
        return AnalyzeCandidateResumeCommand(
            job_spec=load_fixture_json("jobs/ai_engineer"),
        ).execute_extraction_of_flags(
            resume_formatted=load_fixture_json(f"candidates/parsed/{candidate_name}"),
        )
