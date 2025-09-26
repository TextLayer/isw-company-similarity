import json

from tests import BaseTest


class TestThreadRoutes(BaseTest):
    def test_chat_stream(self):
        response = self.client.post(
            "/v1/threads/chat/stream",
            json={"messages": [{"role": "user", "content": "say hello!"}]},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("Content-Type", "")

    def test_chat(self):
        response = self.client.post(
            "/v1/threads/chat",
            json={"messages": [{"role": "user", "content": "say hello!"}]},
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data.get("payload")[0].get("content").startswith("Hello!")

    def test_chat_models(self):
        response = self.client.get(
            "/v1/threads/models",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert len(response_data.get("payload").get("chat_models")) > 0
