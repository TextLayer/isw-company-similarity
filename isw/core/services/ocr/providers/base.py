from abc import ABC, abstractmethod
from typing import Any

from isw.core.services.ocr.types import OCRResult
from isw.core.utils.factory import GenericProviderFactory


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, document: Any, **kwargs) -> OCRResult:
        """
        Extract text from a document.

        Args:
            document: The document to process
            **kwargs: Provider-specific options

        Returns:
            OCRResult: The result of the OCR process
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the provider.

        Returns:
            str: The name of the provider
        """
        pass


OCRProviderFactory = GenericProviderFactory[OCRProvider]("OCR")
