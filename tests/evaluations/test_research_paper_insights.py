from tests.evaluations.base import FunctionalEvaluator
from isw.core.commands.research.generate_research_paper_insights import GenerateResearchPaperInsightsCommand
from isw.core.schemas.research_schemas import InsightType


class TestResumeExtractionExperience(FunctionalEvaluator):
    @FunctionalEvaluator.sample(size=10, threshold=0.85)
    def test_generate_research_paper_applications_insights(self):
        self.judge(
            llm_output=self._get_research_paper_insights(InsightType.APPLICATIONS),
            llm_output_expected="""
            * Suggested applications identified include:
            - Machine translation, specifically English-to-German and English-to-French translation tasks
            - English constituency parsing for more advanced grammar checks and sentiment analysis
            - Faster training and increased parallelization
            - Image captioning and generation
            - Speech recognition and synthesis
            - Video analysis
            """,
            judge="summary",
        )

    def _get_research_paper_insights(self, insight: InsightType) -> str:
        return GenerateResearchPaperInsightsCommand(
            id="68787cc6d61f6a5475534820144c6a13",
            insight=insight.value,
        ).execute(stream=False)
