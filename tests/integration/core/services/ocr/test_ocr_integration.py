import os
from types import SimpleNamespace as MockResponse
from unittest.mock import Mock, patch

import pytest

from tests import BaseTest
from isw.core.services.ocr import OCRResult, OCRService


class TestOCRServiceIntegration(BaseTest):
    """Integration tests for OCR service."""

    @pytest.fixture
    def mock_mistral_response(self):
        """Mock response from Mistral OCR API."""
        # Create a response object that matches Mistral's API structure
        response = MockResponse(
            pages=[
                MockResponse(markdown="Invoice #12345\nDate: 2024-01-15\nTotal: $1,500.00", index=0),
                MockResponse(markdown="Terms and Conditions\nPayment due within 30 days", index=1),
            ],
            model="mistral-ocr-latest",
            usage={"total_tokens": 150},
        )
        return response

    @pytest.mark.integration
    @patch("textlayer.core.services.ocr.providers.mistral.Mistral")
    def test_mistral_provider_integration(self, mock_mistral_class, mock_mistral_response):
        """Test full integration with Mistral provider."""
        # Setup mock
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.ocr.process.return_value = mock_mistral_response

        # Create service
        service = OCRService(provider="mistral", api_key="test_key")

        # Extract text
        result = service.extract_text("https://example.com/invoice.pdf")

        # Verify result format
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify first page
        assert result[0].page_number == 1
        assert result[0].markdown == "Invoice #12345\nDate: 2024-01-15\nTotal: $1,500.00"

        # Verify second page
        assert result[1].page_number == 2
        assert result[1].markdown == "Terms and Conditions\nPayment due within 30 days"

    @pytest.mark.integration
    @patch("textlayer.core.services.ocr.providers.mistral.Mistral")
    def test_extract_with_metadata_integration(self, mock_mistral_class, mock_mistral_response):
        """Test extraction with metadata returns full result."""
        # Setup mock
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.ocr.process.return_value = mock_mistral_response

        # Create service and extract with metadata
        service = OCRService(provider="mistral", api_key="test_key")
        result = service.extract_text("document.pdf", include_metadata=True)

        # Verify result structure
        assert isinstance(result, OCRResult)
        assert isinstance(result.pages, list)
        assert len(result.pages) == 2
        assert result.pages[0].page_number == 1
        assert result.pages[0].markdown == "Invoice #12345\nDate: 2024-01-15\nTotal: $1,500.00"
        assert result.pages[1].page_number == 2
        assert result.pages[1].markdown == "Terms and Conditions\nPayment due within 30 days"
        assert result.metadata["provider"] == "mistral"
        assert result.metadata["raw_response"] == mock_mistral_response

    @pytest.mark.integration
    @patch("textlayer.core.services.ocr.providers.mistral.config")
    @patch("textlayer.shared.config.config")
    @patch("textlayer.core.services.ocr.providers.mistral.Mistral")
    def test_config_integration(self, mock_mistral_class, mock_shared_config, mock_provider_config):
        """Test service uses configuration correctly."""
        # Setup config
        mock_shared_config.return_value.ocr_provider = "mistral"
        mock_shared_config.return_value.mistral_api_key = "config_key"
        mock_provider_config.return_value.mistral_api_key = "config_key"

        # Setup Mistral mock
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.ocr.process.return_value = MockResponse(pages=[MockResponse(markdown="Test", index=0)])

        # Create service without explicit provider
        service = OCRService()

        # Verify it uses config values
        assert service.get_provider_name() == "mistral"
        mock_mistral_class.assert_called_once_with(api_key="config_key")

        # Test extraction returns correct format
        result = service.extract_text("test.pdf")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].page_number == 1
        assert result[0].markdown == "Test"

    @pytest.mark.integration
    @patch.dict(os.environ, {"MISTRAL_API_KEY": "env_key"})
    @patch("textlayer.core.services.ocr.providers.mistral.Mistral")
    def test_error_propagation(self, mock_mistral_class):
        """Test errors are properly propagated."""
        # Setup mock to raise error
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.ocr.process.side_effect = Exception("API rate limit exceeded")

        # Create service and attempt extraction
        service = OCRService(provider="mistral", api_key="test_key")

        with pytest.raises(Exception, match="API rate limit exceeded"):
            service.extract_text("document.pdf")

    @pytest.mark.integration
    @patch("textlayer.core.services.ocr.providers.mistral.Mistral")
    def test_empty_document_handling(self, mock_mistral_class):
        """Test handling of empty documents."""
        # Setup mock with empty response
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.ocr.process.return_value = MockResponse(pages=[])

        # Create service and extract
        service = OCRService(provider="mistral", api_key="test_key")
        result = service.extract_text("empty.pdf")

        # Should return empty list
        assert result == []
