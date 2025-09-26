from unittest.mock import Mock, patch

import pytest

from isw.core.services.ocr import OCRPage, OCRResult, OCRService
from isw.core.services.ocr.providers import OCRProvider, OCRProviderFactory
from isw.shared.config import set_config
from isw.shared.config.base import BaseConfig


class TestOCRService:
    """Unit tests for OCR service."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock OCR provider."""
        provider = Mock(spec=OCRProvider)
        provider.get_provider_name.return_value = "mock"
        return provider

    @pytest.fixture
    def service(self, mock_provider):
        """Create OCR service with mocked provider."""
        with patch.object(OCRProviderFactory, "create", return_value=mock_provider):
            return OCRService(provider="mock")

    def test_extract_text_returns_pages(self, service, mock_provider):
        """Test extract_text returns list of OCRPage objects by default."""
        mock_provider.extract_text.return_value = OCRResult(
            pages=[OCRPage(markdown="Extracted text content", page_number=1)], metadata={"pages": 1}
        )

        result = service.extract_text("document.pdf")

        assert result == [OCRPage(markdown="Extracted text content", page_number=1)]
        mock_provider.extract_text.assert_called_once_with("document.pdf")

    def test_extract_text_with_metadata(self, service, mock_provider):
        """Test extract_text returns OCRResult when metadata requested."""
        expected_result = OCRResult(
            pages=[OCRPage(markdown="Extracted text content", page_number=1)], metadata={"pages": 1, "provider": "mock"}
        )
        mock_provider.extract_text.return_value = expected_result

        result = service.extract_text("document.pdf", include_metadata=True)

        assert result == expected_result
        assert result.pages[0].markdown == "Extracted text content"
        assert result.metadata["pages"] == 1

    def test_extract_text_passes_kwargs(self, service, mock_provider):
        """Test provider-specific kwargs are passed through."""
        mock_provider.extract_text.return_value = OCRResult(pages=[OCRPage(markdown="Text", page_number=1)])

        service.extract_text("doc.pdf", include_image=False, custom_option="value")

        mock_provider.extract_text.assert_called_once_with("doc.pdf", include_image=False, custom_option="value")

    def test_get_provider_name(self, service, mock_provider):
        """Test get_provider_name delegates to provider."""
        assert service.get_provider_name() == "mock"
        mock_provider.get_provider_name.assert_called_once()

    @patch("textlayer.shared.config.config")
    def test_uses_config_defaults(self, mock_config):
        """Test service uses config for default provider."""
        mock_config.return_value.ocr_provider = "mistral"

        # Set up a test config
        test_config = BaseConfig.from_env()
        set_config(test_config)

        with patch.object(OCRProviderFactory, "create") as mock_create:
            OCRService()
            mock_create.assert_called_once_with("mistral")
