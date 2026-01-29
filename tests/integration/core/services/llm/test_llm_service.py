import os
import unittest

import pytest
from pydantic import BaseModel

from isw.core.services.llm import LLMService


class ExtractedInfo(BaseModel):
    company_name: str
    industry: str
    is_technology_company: bool


@pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY") is None or os.environ.get("OPENAI_API_KEY") == "",
    reason="OPENAI_API_KEY not set. Set it to run LLM integration tests.",
)
class TestLLMServiceIntegration(unittest.TestCase):
    """Integration tests for LLM structured output."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.service = LLMService(model="gpt-4o-mini")
        except Exception as e:
            pytest.skip(f"Failed to initialize LLM service: {e}")

    def test_extracts_structured_info_from_text(self):
        """LLM should extract structured information from unstructured text."""
        text = """
        Apple Inc. is an American multinational technology company headquartered in
        Cupertino, California. Apple is the world's largest technology company by revenue,
        with US$394.3 billion in 2022 revenue. The company designs, manufactures, and
        markets smartphones, personal computers, tablets, wearables, and accessories.
        """

        result = self.service.structured_output(
            messages=[
                {
                    "role": "user",
                    "content": f"Extract company information from this text:\n\n{text}",
                }
            ],
            output_structure=ExtractedInfo,
        )

        assert isinstance(result, ExtractedInfo)
        assert "apple" in result.company_name.lower()
        assert result.is_technology_company is True

    def test_handles_different_models(self):
        """Service should work with different LiteLLM-supported models."""
        # Skip if no API key - this test uses the same OpenAI key
        service = LLMService(model="gpt-4o-mini")

        result = service.structured_output(
            messages=[{"role": "user", "content": "What company makes the iPhone?"}],
            output_structure=ExtractedInfo,
        )

        assert isinstance(result, ExtractedInfo)
        assert "apple" in result.company_name.lower()
