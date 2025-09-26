import json

import pytest

from tests import BaseTest


@pytest.mark.integration
class TestTaskRegistry(BaseTest):
    def test_health_endpoint_contract(self):
        response = self.client.get("/v1/health")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["payload"]["worker_status"] == "online"
