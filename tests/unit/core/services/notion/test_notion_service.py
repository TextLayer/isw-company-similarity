import types

import httpx
import pytest
import requests
from notion_client import APIErrorCode, APIResponseError

from tests import BaseCommandTest
from isw.core.services.notion.service import NotionService, NotionServiceError


class DummyClientSuccess:
    def __init__(self, page):
        self._page = page

    class pages:
        @staticmethod
        def retrieve(page_id):
            return None


class DummyN2M:
    def __init__(self, client):
        pass

    def page_to_markdown(self, page_id):
        return [{"type": "paragraph", "content": "Hello"}]

    def to_markdown_string(self, blocks):
        return {"body": "Hello"}


class DummyClientAPIError:
    class pages:
        @staticmethod
        def retrieve(page_id):
            resp = httpx.Response(
                status_code=401,
                request=httpx.Request("GET", "https://api.notion.com"),
                content=b"unauthorized",
            )
            raise APIResponseError(resp, "nope", APIErrorCode.Unauthorized)


class DummyClientNetworkError:
    class pages:
        @staticmethod
        def retrieve(page_id):
            raise requests.RequestException("boom")


class TestNotionService(BaseCommandTest):
    def test_retrieve_page_markdown_html_success(self, monkeypatch):
        page = {"id": "p1"}

        client = DummyClientSuccess(page)

        def retrieve(page_id=None, **_kwargs):
            return page

        monkeypatch.setattr(client.pages, "retrieve", staticmethod(retrieve))
        monkeypatch.setattr("textlayer.core.services.notion.service.Client", lambda auth: client)
        monkeypatch.setattr("textlayer.core.services.notion.service.NotionToMarkdown", lambda client: DummyN2M(client))

        svc = NotionService(api_token="x")
        out = svc.retrieve_page_markdown_html("p1")
        assert out["page"] == page
        assert "markdown" in out and "html" in out

    def test_retrieve_page_markdown_html_api_error(self, monkeypatch):
        monkeypatch.setattr("textlayer.core.services.notion.service.Client", lambda auth: DummyClientAPIError())
        monkeypatch.setattr(
            "textlayer.core.services.notion.service.NotionToMarkdown",
            lambda client: types.SimpleNamespace(page_to_markdown=lambda pid: [], to_markdown_string=lambda blocks: {}),
        )

        svc = NotionService(api_token="x")
        with pytest.raises(NotionServiceError):
            svc.retrieve_page_markdown_html("p1")

    def test_retrieve_page_markdown_html_network_error(self, monkeypatch):
        monkeypatch.setattr("textlayer.core.services.notion.service.Client", lambda auth: DummyClientNetworkError())
        monkeypatch.setattr(
            "textlayer.core.services.notion.service.NotionToMarkdown",
            lambda client: types.SimpleNamespace(page_to_markdown=lambda pid: [], to_markdown_string=lambda blocks: {}),
        )

        svc = NotionService(api_token="x")
        with pytest.raises(NotionServiceError):
            svc.retrieve_page_markdown_html("p1")
