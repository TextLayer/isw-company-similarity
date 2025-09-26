import unittest

from isw.core.utils.research import ResearchPapersQueryBuilder


class TestResearchPapersQueryBuilder(unittest.TestCase):
    def test_build_query(self):
        categories = ["Electrical Engineering and Systems Science"]
        search_query = 'latest on "machine learning"'
        page = 2
        query = (
            ResearchPapersQueryBuilder(results_per_page=24)
            .add_categories(categories)
            .set_search_query(search_query)
            .set_page(page)
            .build()
        )

        assert (
            query.query["function_score"]["query"]["bool"]["filter"][0]["bool"]["should"][0]["term"]["l1_domains"]
            == categories[0]
        )
        assert (
            query.query["function_score"]["query"]["bool"]["filter"][0]["bool"]["should"][1]["term"]["l2_domains"]
            == categories[0]
        )

        # check keyword search
        assert query.query["function_score"]["query"]["bool"]["must"][0]["multi_match"]["query"] == "machine learning"
        # check fuzzy search
        assert (
            query.query["function_score"]["query"]["bool"]["should"][0]["multi_match"]["query"]
            == "latest on machine learning"
        )
