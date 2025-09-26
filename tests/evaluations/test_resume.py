from isw.core.commands.recruitment.analyze_candidate_resume import AnalyzeCandidateResumeCommand
from tests.evaluations.base import FunctionalEvaluator
from tests.fixtures import load_fixture, load_fixture_json


class TestResume(FunctionalEvaluator):
    @FunctionalEvaluator.sample(size=5, threshold=0.79)
    def test_rick_sanchez(self):
        result = AnalyzeCandidateResumeCommand(
            job_spec=load_fixture_json("jobs/ai_engineer"),
            resume=load_fixture("candidates/raw/rick_sanchez"),
        ).execute()

        self.judge(
            debugging_info=result.get("grade").get("notes"),
            llm_output=result.get("grade").get("recommendation_result"),
            llm_output_expected="Recommend",
            judge="correctness",
        )
