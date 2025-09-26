from tests.evaluations.base import FunctionalEvaluator
from tests.fixtures import load_fixture_json
from isw.core.commands.recruitment.analyze_candidate_resume import AnalyzeCandidateResumeCommand


class TestResumeExtractionExperience(FunctionalEvaluator):
    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_rick_sanchez_experience(self):
        self.judge(
            llm_output=self._get_experience_for_candidate("rick_sanchez"),
            llm_output_expected="""
            - Trajectory from data scientist to director
            - Hands on technical contributions with AI
            - Coporate-heavy experience (Scotiabank, OpenText)
            - Management and leadership experience
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_sterling_archer_experience(self):
        self.judge(
            llm_output=self._get_experience_for_candidate("sterling_archer"),
            llm_output_expected="""
            - Churn reduction of 7% quarter over quarter
            - 95% test accuracy
            - 90% weighted live accuracy
            - NVMe Processor Complex with 50,000+ lines of code
            - Entreprenurial (founding engineer)
            """,
            judge="summary",
        )

    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_bob_belcher_experience(self):
        self.judge(
            llm_output=self._get_experience_for_candidate("bob_belcher"),
            llm_output_expected="""
            - Insights & Analytics to Advanced Data Scientist
            - Recruited and coordinated 50+ mentors and judges
            - Hackathon lead, showing initiative and innovation
            - Hands on technical contributions with LLMs
            """,
            judge="summary",
        )

    def _get_experience_for_candidate(self, candidate_name: str) -> str:
        return AnalyzeCandidateResumeCommand(
            job_spec=load_fixture_json("jobs/ai_engineer"),
        ).execute_extraction_of_experience(
            resume_formatted=load_fixture_json(f"candidates/parsed/{candidate_name}"),
        )
