import hashlib
import hmac
import importlib
import json
import time
from unittest.mock import patch

import pytest

from tests import BaseTest
from tests.fixtures.mocks import DummyRegistry
from isw.interfaces.api.utils.response import Response
from isw.shared.config import config


def create_test_ashby_signature(body: bytes, secret: str) -> str:
    hash_object = hmac.new(key=secret.encode(), msg=body, digestmod=hashlib.sha256)
    return f"sha256={hash_object.hexdigest()}"


def create_test_langfuse_signature(raw_body: str, secret: str) -> str:
    timestamp = str(int(time.time()))
    message = f'{timestamp}."{raw_body}"'.encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"t={timestamp},s={signature}"


class TestRecruitmentRoutes(BaseTest):
    @pytest.mark.integration
    def test_validate_ashby_signature(self):
        with patch("textlayer.interfaces.api.routes.webhooks.task_registry", return_value=True) as mock_task_registry:
            mock_task_registry.defer.return_value = True
            data = {"action": "applicationSubmit", "data": {"application": {"candidate": {"id": "456"}, "id": "123"}}}
            json_bytes = json.dumps(data).encode("utf-8")

            response = self.client.post(
                "/v1/webhooks/recruitment/ashby",
                headers={"Ashby-Signature": create_test_ashby_signature(json_bytes, config().ashby_secret)},
                json=data,
            )

            assert response.status_code == 204
            assert mock_task_registry.defer.call_count == 1

    @pytest.mark.integration
    def test_validate_langfuse_signature(self):
        with patch("textlayer.interfaces.api.routes.webhooks.task_registry", return_value=True) as mock_task_registry:
            mock_task_registry.defer.return_value = True
            json_body = "foobar"

            response = self.client.post(
                "/v1/webhooks/prompts/langfuse",
                headers={
                    "X-Langfuse-Signature": create_test_langfuse_signature(
                        json_body, config().langfuse_signing_secret_prompts
                    )
                },
                json=json_body,
            )

            assert response.status_code == 204

    def test_webhook_candidate_stage_change_defers_task(self, monkeypatch):
        calls = []

        webhooks_mod = importlib.import_module("textlayer.interfaces.api.routes.webhooks")
        monkeypatch.setattr(webhooks_mod.webhooks_controller, "validate", lambda **kwargs: True)
        monkeypatch.setattr(webhooks_mod, "task_registry", DummyRegistry(calls))

        body = {
            "action": "candidateStageChange",
            "data": {
                "application": {
                    "archiveReason": None,
                    "candidate": {
                        "id": "cand-1111-2222-3333-4444",
                        "name": "Test Candidate",
                        "primaryEmailAddress": {
                            "isPrimary": True,
                            "type": "Personal",
                            "value": "candidate@example.com",
                        },
                        "primaryPhoneNumber": {
                            "isPrimary": True,
                            "type": "Personal",
                            "value": "5550001234",
                        },
                    },
                    "createdAt": "2025-08-06T15:14:54.420Z",
                    "creditedToUser": {
                        "email": "recruiter@example.com",
                        "firstName": "Recruiter",
                        "globalRole": "Organization Admin",
                        "id": "user-aaaa-bbbb-cccc-dddd",
                        "isEnabled": True,
                        "lastName": "One",
                        "updatedAt": "2025-07-31T22:42:18.718Z",
                    },
                    "currentInterviewStage": {
                        "id": "stage-aaaa-bbbb-cccc-dddd",
                        "interviewPlanId": "plan-1111-2222-3333-4444",
                        "interviewStageGroupId": None,
                        "orderInInterviewPlan": 4,
                        "title": "Pre-Screen",
                        "type": "Active",
                    },
                    "customFields": [],
                    "id": "app-9999-8888-7777-6666",
                    "source": {
                        "id": "src-aaaa-bbbb-cccc-dddd",
                        "isArchived": False,
                        "sourceType": {
                            "id": "stype-1111-2222-3333-4444",
                            "isArchived": False,
                            "title": "Sourced",
                        },
                        "title": "Wellfound",
                    },
                    "status": "Active",
                    "updatedAt": "2025-08-20T14:07:57.779Z",
                }
            },
            "webhookActionId": "wh-aaaa-bbbb-cccc-dddd",
        }
        resp = self.client.post(
            "/v1/webhooks/recruitment/ashby", data=json.dumps(body), content_type="application/json"
        )
        assert resp.status_code == Response.HTTP_NO_CONTENT
        assert calls and calls[0][0] == "candidate_stage_change"
        assert calls[0][1] == {
            "application_id": body["data"]["application"]["id"],
            "candidate_id": body["data"]["application"]["candidate"]["id"],
        }
