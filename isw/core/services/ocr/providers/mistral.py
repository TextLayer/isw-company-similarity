from typing import Any, Optional

from mistralai import Mistral

from isw.core.services.ocr.providers.base import OCRProvider, OCRProviderFactory
from isw.core.services.ocr.types import OCRPage, OCRResult
from isw.shared.config import config
from isw.shared.logging.logger import logger


class MistralOCRProvider(OCRProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config().mistral_api_key
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY is required for Mistral OCR service")

        self.client = Mistral(api_key=self.api_key)

    def extract_text(self, document: Any, **kwargs) -> OCRResult:
        try:
            include_image = kwargs.get("include_image", True)

            mistral_document = {
                "type": "document_url",
                "document_url": document,
            }

            result = self.client.ocr.process(
                model="mistral-ocr-latest",
                document=mistral_document,
                include_image_base64=include_image,
            )

            return OCRResult(
                pages=[
                    OCRPage(
                        markdown=page.markdown,
                        page_number=page.index + 1,
                    )
                    for page in result.pages
                ],
                metadata={"provider": self.get_provider_name(), "model": "mistral-ocr-latest", "raw_response": result},
            )
        except Exception as e:
            logger.error(f"Failed to extract text from document: {e}")
            raise

    def get_provider_name(self) -> str:
        return "mistral"


# Register the provider
OCRProviderFactory.register("mistral", MistralOCRProvider)
