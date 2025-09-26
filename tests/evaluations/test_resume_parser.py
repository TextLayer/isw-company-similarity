import json

from isw.core.commands.recruitment.analyze_candidate_resume import AnalyzeCandidateResumeCommand
from tests.evaluations.base import FunctionalEvaluator
from tests.fixtures import load_fixture, load_fixture_json


class TestResumeParser(FunctionalEvaluator):
    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_sterling_archer_parser(self):
        self.judge(
            llm_output=json.dumps(
                AnalyzeCandidateResumeCommand(
                    job_spec=load_fixture_json("jobs/ai_engineer"),
                    resume=load_fixture("candidates/raw/sterling_archer"),
                ).execute_parser()
            ),
            llm_output_expected=load_fixture_json("candidates/parsed/sterling_archer"),
            judge="correctness",
        )
