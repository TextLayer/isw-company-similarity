from isw.core.commands.base import WriteCommand
from isw.core.services.search.service import SearchService
from isw.core.services.search.types import IndexConfig
from isw.shared.config import with_config


class CreateJobsIndexCommand(WriteCommand):
    def __init__(self):
        pass

    def validate(self):
        pass

    @with_config("recruitment_jobs_index")
    def execute(self, recruitment_jobs_index: str):
        settings = {
            "number_of_replicas": 0,
            "number_of_shards": 1,
        }

        mappings = {
            "properties": {
                "description": {
                    "index": False,
                    "type": "text",
                },
                "expectations": {
                    "index": False,
                    "type": "text",
                },
                "flags": {
                    "properties": {
                        "green": {
                            "properties": {
                                "flag": {
                                    "index": False,
                                    "type": "text",
                                },
                                "reasons": {
                                    "index": False,
                                    "type": "text",
                                },
                            },
                            "type": "nested",
                        },
                        "red": {
                            "properties": {
                                "flag": {
                                    "index": False,
                                    "type": "text",
                                },
                                "reasons": {
                                    "index": False,
                                    "type": "text",
                                },
                            },
                            "type": "nested",
                        },
                    },
                    "type": "nested",
                },
                "qualifications": {
                    "properties": {
                        "bonus": {
                            "index": False,
                            "type": "text",
                        },
                        "preferred": {
                            "index": False,
                            "type": "text",
                        },
                        "required": {
                            "index": False,
                            "type": "text",
                        },
                    },
                    "type": "nested",
                },
                "responsibilities": {
                    "index": False,
                    "type": "text",
                },
                "title": {
                    "index": True,
                    "type": "keyword",
                },
            }
        }

        SearchService("opensearch").create_index(
            IndexConfig(
                name=recruitment_jobs_index,
                settings=settings,
                mappings=mappings,
            ),
        )

        return True
