from ..commands.research.generate_research_paper_insights import GenerateResearchPaperInsightsCommand
from ..commands.research.search_research_papers import SearchResearchPapersCommand
from ..services.cache import cache_result
from .base import Controller


class ResearchController(Controller):
    @cache_result(ttl=3600)
    def generate_research_paper_insights(self, **kwargs):
        return self.executor.execute_write(GenerateResearchPaperInsightsCommand(**kwargs))

    def search_research_papers(self, **kwargs):
        return self.executor.execute_write(SearchResearchPapersCommand(**kwargs))
