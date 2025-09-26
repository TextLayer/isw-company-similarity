import types

import pytest
from marshmallow import ValidationError

from tests import BaseTest
from tests.fixtures.mocks import DummyJWT, DummyMail, DummyStorage
from isw.core.commands.recruitment.candidate_stage_change import CandidateStageChangeCommand
from isw.core.errors.validation import ValidationException


class DummyATS:
    def get_application(self, application_id):
        return {"currentInterviewStage": {"title": "Some Stage"}}


class DummyProvider:
    def __init__(self):
        self.calls = []

    def update_by_query(self, index, query, update):
        self.calls.append((index, query, update))


class DummySearch:
    def __init__(self):
        self.provider = DummyProvider()

    def search(self, index, query):
        return types.SimpleNamespace(total=1, hits=[{"id": "x"}])


class DummyNotion:
    def retrieve_page_markdown_html(self, page_id):
        return {"markdown": "# md", "html": "<p>md</p>"}


class ProviderNoop:
    def update_by_query(self, *a, **k):
        return None


class SearchWithNoopProvider:
    def __init__(self):
        self.provider = ProviderNoop()

    def search(self, *a, **k):
        return types.SimpleNamespace(total=1, hits=[{"id": "x"}])


class SearchWithNoopProvider3:
    def __init__(self):
        self.provider = ProviderNoop()

    def search(self, *a, **k):
        return types.SimpleNamespace(total=1, hits=[{"id": "x"}])


class TestCandidateStageChange(BaseTest):
    def test_validate_missing_application_id(self, monkeypatch):
        cmd = self.__make_cmd(app_id="", cand_id="c1")
        monkeypatch.setattr(CandidateStageChangeCommand, "_get_existing_candidate", lambda self: True)
        with pytest.raises(ValidationError):
            cmd.validate()

    def test_validate_missing_candidate_id(self, monkeypatch):
        cmd = self.__make_cmd(app_id="a1", cand_id="")
        monkeypatch.setattr(CandidateStageChangeCommand, "_get_existing_candidate", lambda self: True)
        with pytest.raises(ValidationError):
            cmd.validate()

    def test_validate_missing_candidate_in_search(self, monkeypatch):
        cmd = self.__make_cmd()
        monkeypatch.setattr(CandidateStageChangeCommand, "_get_existing_candidate", lambda self: None)
        with pytest.raises(ValidationException):
            cmd.validate()

    def test_update_candidate_stage_calls_update_by_query(self, monkeypatch):
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.config",
            lambda: types.SimpleNamespace(
                recruitment_candidate_index="idx",
                doppler_api_token="dummy_token",
                notion_api_token="dummy_token",
                doppler_project="dummy_project",
                doppler_config="dummy_config",
                assignment_s3_bucket="dummy_bucket",
                assignment_s3_key="dummy_key",
                notion_engineer_assignment_id="dummy_id",
                client_url="https://dummy.com",
            ),
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.ATSService",
            lambda: DummyATS(),
            raising=False,
        )
        dummy_search = DummySearch()
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.SearchService",
            lambda: dummy_search,
            raising=False,
        )
        cmd = self.__make_cmd()
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.DopplerService",
            lambda *a, **k: types.SimpleNamespace(),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.NotionService",
            lambda *a, **k: types.SimpleNamespace(),
            raising=False,
        )
        cmd.execute()
        assert len(dummy_search.provider.calls) == 1
        idx, query, update = dummy_search.provider.calls[0]
        assert idx == "idx"
        assert "bool" in query.query
        assert "source" in update

    def test_prepare_assignment_data(self, monkeypatch):
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.StorageService",
            DummyStorage,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.NotionService",
            lambda *args, **kwargs: DummyNotion(),
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.time",
            types.SimpleNamespace(time=lambda: 1_000_000),
        )
        conf = types.SimpleNamespace(
            assignment_s3_bucket="bkt",
            assignment_s3_key="key",
            notion_engineer_assignment_id="pid",
            recruitment_candidate_index="idx",
            client_url="https://client",
            doppler_api_token="dummy_token",
            notion_api_token="dummy_token",
            doppler_project="dummy_project",
            doppler_config="dummy_config",
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.config",
            lambda: conf,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.SearchService",
            lambda: types.SimpleNamespace(search=lambda **kwargs: types.SimpleNamespace(total=1, hits=[{}])),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.DopplerService",
            lambda api_token=None: types.SimpleNamespace(
                create_service_token=lambda **k: {"token": {"key": "doppler123"}}
            ),
            raising=False,
        )
        cmd = self.__make_cmd()
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.ATSService",
            lambda: types.SimpleNamespace(
                get_application=lambda *_a, **_k: {"currentInterviewStage": {"title": "Some Stage"}}
            ),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.SearchService",
            lambda: SearchWithNoopProvider(),
            raising=False,
        )
        cmd.execute()
        out = cmd._prepare_assignment_data("Alice")
        assert "presigned_url" in out and out["presigned_url"].startswith("https://")
        assert "notion_content" in out and "html" in out["notion_content"]
        assert out["doppler_token"] == "doppler123"
        assert "expire_at" in out

    def test_send_assignment_email_builds_template_data(self, monkeypatch):
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.JWTService",
            lambda: DummyJWT(),
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.MailService",
            lambda: DummyMail(),
        )
        conf = types.SimpleNamespace(
            client_url="https://client",
            recruitment_candidate_index="idx",
            doppler_api_token="dummy_token",
            notion_api_token="dummy_token",
            doppler_project="dummy_project",
            doppler_config="dummy_config",
            assignment_s3_bucket="dummy_bucket",
            assignment_s3_key="dummy_key",
            notion_engineer_assignment_id="dummy_id",
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.config",
            lambda: conf,
        )
        cmd = self.__make_cmd()
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.NotionService",
            lambda *a, **k: types.SimpleNamespace(
                retrieve_page_markdown_html=lambda pid: {"markdown": "m", "html": "h"}
            ),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.ATSService",
            lambda: types.SimpleNamespace(
                get_application=lambda *_a, **_k: {"currentInterviewStage": {"title": "Some Stage"}},
                get_candidate=lambda *_a, **_k: {"primaryEmailAddress": {"value": "a@b.com"}, "name": "Alice"},
            ),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.SearchService",
            lambda: types.SimpleNamespace(provider=types.SimpleNamespace(update_by_query=lambda **k: None)),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.DopplerService",
            lambda *a, **k: types.SimpleNamespace(),
            raising=False,
        )
        cmd.execute()
        job_tpl = {"template_name": "technical_interview", "subject": "Subj"}
        monkeypatch.setattr(cmd, "_get_job_template", lambda job_id: job_tpl)
        cmd._send_assignment_email(
            candidate_email="a@b.com",
            assignment_data={
                "presigned_url": "u",
                "doppler_token": "d",
                "notion_content": {"markdown": "m", "html": "h"},
                "expire_at": 0,
            },
            job_id="job1",
            candidate_name="Alice",
        )

    def test_create_assignment_note(self, monkeypatch):
        conf = types.SimpleNamespace(
            recruitment_candidate_index="idx",
            client_url="https://client",
            doppler_api_token="dummy_token",
            notion_api_token="dummy_token",
            doppler_project="dummy_project",
            doppler_config="dummy_config",
            assignment_s3_bucket="dummy_bucket",
            assignment_s3_key="dummy_key",
            notion_engineer_assignment_id="dummy_id",
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.config",
            lambda: conf,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.time",
            types.SimpleNamespace(strftime=lambda *a, **k: "2025-01-01 00:00:00", localtime=lambda x: 0),
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.DopplerService",
            lambda *a, **k: types.SimpleNamespace(),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.NotionService",
            lambda *a, **k: types.SimpleNamespace(),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.SearchService",
            lambda: SearchWithNoopProvider3(),
            raising=False,
        )
        monkeypatch.setattr(
            "textlayer.core.commands.recruitment.candidate_stage_change.ATSService",
            lambda: types.SimpleNamespace(
                add_note_to_candidate=lambda **kwargs: None,
                get_application=lambda *_a, **_k: {"currentInterviewStage": {"title": "Some Stage"}},
            ),
            raising=False,
        )
        cmd = self.__make_cmd()
        cmd.execute()
        cmd._create_assignment_note("a@b.com", 0)

    def __make_cmd(self, app_id="app123", cand_id="cand456"):
        return CandidateStageChangeCommand(application_id=app_id, candidate_id=cand_id)
