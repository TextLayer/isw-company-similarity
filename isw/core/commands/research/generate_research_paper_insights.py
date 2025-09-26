from typing import Generator, Union

from ....shared.config import with_config
from ....shared.logging.logger import logger
from ....templates.prompts import load_prompt
from ...commands.base import WriteCommand
from ...schemas.research_schemas import research_paper_insights_schema, research_paper_schema
from ...services.llm import ChatClient
from ...services.search import SearchService
from ...utils.llm import extract_output


class GenerateResearchPaperInsightsCommand(WriteCommand):
    def __init__(self, id: str, insight: str):
        self.id = id
        self.insight = insight

    def validate(self):
        research_paper_insights_schema.load(self.__dict__)

    @with_config("research_papers_index")
    def execute(self, research_papers_index, stream: bool = True) -> Union[str, Generator[str, None, None]]:
        try:
            result = SearchService("opensearch").get_document(research_papers_index, self.id)
            summary = research_paper_schema.load(result.get("_source")).get("summary")

            response = ChatClient().chat(
                messages=[
                    {"role": "system", "content": load_prompt("research_insights", summary=summary)},
                    {"role": "user", "content": self.insight},
                ],
                stream=stream,
            )

            if stream:
                return response

            return extract_output(response)
        except Exception as e:
            logger.error(f"Error generating research paper insights: {e}")
            return ""
