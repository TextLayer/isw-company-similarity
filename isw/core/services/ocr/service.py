from typing import Any, Optional

from isw.core.services.ocr.providers import OCRProviderFactory
from isw.core.services.ocr.types import OCRPages, OCRResult
from isw.shared.config import config
from isw.shared.logging.logger import logger


class OCRService:
    """OCR service that delegates to configured provider."""

    def __init__(self, provider: Optional[str] = None, **provider_kwargs):
        """
        Initialize OCR service.

        Args:
            provider: OCR provider to use (defaults to config)
            **provider_kwargs: Additional provider-specific arguments
        """
        self.provider_name = provider or config().ocr_provider
        self.provider = OCRProviderFactory.create(self.provider_name, **provider_kwargs)

    def extract_text(self, document: Any, include_metadata: bool = False, **kwargs) -> OCRPages | OCRResult:
        """
        Extract text from a document.

        Args:
            document: Document to process
            include_metadata: Whether to return full OCRResult with metadata
            **kwargs: Provider-specific options

        Returns:
            Extracted text string or OCRResult if include_metadata=True
        """
        logger.info(f"Extracting text via {self.provider_name}")
        result = self.provider.extract_text(document, **kwargs)

        if include_metadata:
            return result

        return result.pages

    def get_provider_name(self) -> str:
        return self.provider.get_provider_name()
