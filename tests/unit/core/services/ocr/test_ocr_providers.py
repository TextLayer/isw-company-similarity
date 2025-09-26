from types import SimpleNamespace as MockResponse
from unittest.mock import Mock, patch

import pytest

from isw.core.services.ocr.providers import MistralOCRProvider
from isw.core.services.ocr.types import OCRPage, OCRResult


class TestMistralOCRProvider:
    """Unit tests for Mistral OCR provider."""

    @pytest.fixture
    def mock_mistral_client(self):
        """Create mock Mistral client."""
        with patch("textlayer.core.services.ocr.providers.mistral.Mistral") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def provider(self, mock_mistral_client):
        """Create Mistral provider with mocked client."""
        return MistralOCRProvider(api_key="test_key")

    @patch("textlayer.core.services.ocr.providers.mistral.config")
    def test_init_requires_api_key(self, mock_config):
        """Test initialization fails without API key."""
        mock_config.return_value.mistral_api_key = None

        with pytest.raises(ValueError, match="MISTRAL_API_KEY is required"):
            MistralOCRProvider()

    def test_extract_text_success(self, provider, mock_mistral_client):
        """Test successful text extraction."""
        mock_mistral_client.ocr.process.return_value = MockResponse(
            pages=[
                MockResponse(markdown="Page 1 content", index=0),
                MockResponse(markdown="Page 2 content", index=1),
            ]
        )

        result = provider.extract_text("https://example.com/doc.pdf")

        assert isinstance(result, OCRResult)
        assert isinstance(result.pages, list)
        assert len(result.pages) == 2
        assert result.pages[0] == OCRPage(markdown="Page 1 content", page_number=1)
        assert result.pages[1] == OCRPage(markdown="Page 2 content", page_number=2)
        assert result.metadata["provider"] == "mistral"
        assert result.metadata["model"] == "mistral-ocr-latest"

        mock_mistral_client.ocr.process.assert_called_once_with(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": "https://example.com/doc.pdf",
            },
            include_image_base64=True,
        )

    def test_extract_text_with_options(self, provider, mock_mistral_client):
        """Test text extraction with custom options."""
        mock_mistral_client.ocr.process.return_value = MockResponse(pages=[])

        provider.extract_text("doc.pdf", include_image=False)

        mock_mistral_client.ocr.process.assert_called_once_with(
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": "doc.pdf"},
            include_image_base64=False,
        )

    def test_extract_text_handles_errors(self, provider, mock_mistral_client):
        """Test error handling during extraction."""
        mock_mistral_client.ocr.process.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            provider.extract_text("doc.pdf")

    def test_get_provider_name(self, provider):
        """Test provider name."""
        assert provider.get_provider_name() == "mistral"
