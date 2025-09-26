from tests import BaseTest


class TestResearchRoutes(BaseTest):
    def test_research_paper_insights_stream(self):
        response = self.client.post(
            "/v1/research/68787cc6d61f6a5475534820144c6a13/insights",
            json={"type": "Applications"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("Content-Type", "")
        assert "Transformer" in response.data.decode("utf-8")

    def test_research_paper_insights_stream_unknown_insight(self):
        response = self.client.post(
            "/v1/research/68787cc6d61f6a5475534820144c6a13/insights",
            json={"type": "Unknown"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 404
