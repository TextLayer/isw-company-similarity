import json

import pytest

from tests import BaseTest
from tests.fixtures import load_fixture_json
from isw.core.services.jwt import JWTService
from isw.interfaces.api.utils.response import Response
from isw.shared.config import config


class TestRecruitmentJobRoutes(BaseTest):
    @pytest.fixture(autouse=True)
    def setup_each_test(self):
        """Runs before each test method"""

        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": config().api_key,
        }

        # setup a job for testing crud operations
        response = self.client.post(
            "/v1/recruitment/jobs",
            json=load_fixture_json("jobs/exec_assistant"),
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_CREATED
        self.job_id = json.loads(response.data).get("payload").get("id")
        yield

        # cleanup the job we created
        response = self.client.delete(f"/v1/recruitment/jobs/{self.job_id}", headers=self.headers)
        assert response.status_code == Response.HTTP_NO_CONTENT
        self.job_id = None

    @pytest.mark.integration
    def test_get_job(self):
        response = self.client.get(f"/v1/recruitment/jobs/{self.job_id}", headers=self.headers)
        assert response.status_code == Response.HTTP_SUCCESS
        res = json.loads(response.data)
        assert res.get("payload").get("title") == "Executive Assistant"
        assert res.get("payload").get("flags").get("green")[0].get("flag") == (
            "Experience with startup or tech company environments"
        )

    @pytest.mark.integration
    def test_job_search(self):
        response = self.client.get("/v1/recruitment/jobs", headers=self.headers)
        assert response.status_code == Response.HTTP_SUCCESS
        res = json.loads(response.data)
        posting = res.get("payload").get("hits")[0]
        assert "id" in posting
        assert "title" in posting

    @pytest.mark.integration
    def test_update_job(self):
        response = self.client.patch(
            f"/v1/recruitment/jobs/{self.job_id}",
            json={
                "title": "Fullstack engineer",
            },
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_SUCCESS
        assert json.loads(response.data).get("payload").get("title") == "Fullstack engineer"


class TestRecruitmentRoutes(BaseTest):
    @pytest.mark.integration
    def test_recruitment_submission_authentication(self):
        response = self.client.get("/v1/recruitment/submission-url")
        assert response.status_code == Response.HTTP_UNAUTHORIZED

    @pytest.mark.integration
    def test_recruitment_submission_validation_response(self):
        token = JWTService().generate_token("test", {})
        response = self.client.get(
            "/v1/recruitment/submission-url",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == Response.HTTP_UNPROCESSABLE
        res = json.loads(response.data)
        errors = res["errors"].keys()
        assert "application_id" in errors
        assert "candidate_id" in errors

    @pytest.mark.integration
    def test_recruitment_submission_success(self):
        token = JWTService().generate_token(
            "test",
            {
                "application_id": "1",
                "candidate_id": "2",
            },
        )

        response = self.client.get(
            "/v1/recruitment/submission-url",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == Response.HTTP_SUCCESS
        data = json.loads(response.data)
        assert data.get("payload").get("url").startswith("https://")
        assert data.get("payload").get("fields").get("key").endswith("/1/2.zip")
