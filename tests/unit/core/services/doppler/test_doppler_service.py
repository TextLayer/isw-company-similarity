import pytest
import requests

from isw.core.services.doppler.service import DopplerService, DopplerServiceError
from tests import BaseCommandTest
from tests.fixtures.mocks import RespBad, RespOK


class TestDopplerService(BaseCommandTest):
    def test_init_without_token_raises(self):
        with pytest.raises(DopplerServiceError):
            DopplerService(api_token="")

    def test_create_service_token_success(self, monkeypatch):
        def fake_post(url, headers=None, json=None, timeout=None):
            return RespOK()

        monkeypatch.setattr(requests, "post", fake_post)

        svc = DopplerService(api_token="tok")
        out = svc.create_service_token(project="proj", config="dev", name="n", access="read", expire_at=123)
        assert out["token"]["key"] == "abc"

    def test_create_service_token_http_error_json(self, monkeypatch):
        def fake_post(url, headers=None, json=None, timeout=None):
            return RespBad()

        monkeypatch.setattr(requests, "post", fake_post)

        svc = DopplerService(api_token="tok")
        with pytest.raises(DopplerServiceError):
            svc.create_service_token(project="proj", config="dev", name="n", access="read", expire_at=123)

    def test_create_service_token_network_error(self, monkeypatch):
        def fake_post(url, headers=None, json=None, timeout=None):
            raise requests.RequestException("down")

        monkeypatch.setattr(requests, "post", fake_post)
        svc = DopplerService(api_token="tok")
        with pytest.raises(DopplerServiceError):
            svc.create_service_token(project="proj", config="dev", name="n", access="read", expire_at=123)
