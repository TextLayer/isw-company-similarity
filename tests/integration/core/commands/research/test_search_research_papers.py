import pytest

from tests import BaseTest
from isw.core.commands.research.search_research_papers import SearchResearchPapersCommand
from isw.shared.config import config


class TestSearchResearchPapers(BaseTest):
    @pytest.mark.integration
    def test_search_research_papers(self):
        conf = config()
        command = SearchResearchPapersCommand(
            categories=["Mathematics", "Probability"],
            search_query="Gauss-Hermite determinantal point processes",
            page=1,
        )

        result = command.run()
        hits = result.get("hits", [])
        # default page size
        assert len(hits) == conf.research_papers_results_per_page
        # smoke test for a paper that should match
        assert any(hit["id"] == "08aa152cc7b088314b5f4e13fc1d4844" for hit in hits)
