import json

import pytest

from tests import BaseTest


@pytest.mark.integration
class TestAPIContract(BaseTest):
    """Verify the API contract is maintained"""

    def test_health_endpoint_contract(self):
        """Health check is critical for monitoring and load balancers"""
        response = self.client.get("/v1/health")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "status" in data
        assert "payload" in data
        assert "correlation_id" in data

        assert data["status"] == 200
        assert data["payload"]["status"] == "online"

    def test_404_error_contract(self):
        """404 errors must have consistent structure"""
        response = self.client.get("/v1/nonexistent")

        assert response.status_code == 404

        data = json.loads(response.data)
        assert "message" in data
        assert "not found" in data["message"].lower()

    def test_response_structure_consistency(self):
        """All successful responses must follow the same structure"""
        endpoints = ["/v1/", "/v1/health"]

        for endpoint in endpoints:
            response = self.client.get(endpoint)

            if response.status_code == 200:
                data = json.loads(response.data)

                assert "status" in data, f"{endpoint} missing status"
                assert "payload" in data, f"{endpoint} missing payload"
                assert "correlation_id" in data, f"{endpoint} missing correlation_id"

                assert isinstance(data["status"], int)
                assert isinstance(data["payload"], dict)
                assert isinstance(data["correlation_id"], str)
