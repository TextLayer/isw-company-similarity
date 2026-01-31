"""Unit tests for LLMService.

Tests initialization and input validation only.
Actual LLM API interactions are tested via integration tests.
"""

import unittest

from pydantic import BaseModel

from isw.core.services.llm import LLMService, LLMServiceError


class SampleOutput(BaseModel):
    name: str
    value: int


class TestLLMServiceInit(unittest.TestCase):
    def test_default_model(self):
        service = LLMService()
        assert service.model == "gpt-4o-mini"

    def test_custom_model(self):
        service = LLMService(model="claude-3-sonnet-20240229")
        assert service.model == "claude-3-sonnet-20240229"


class TestStructuredOutputValidation(unittest.TestCase):
    def setUp(self):
        self.service = LLMService()

    def test_raises_for_empty_messages(self):
        with self.assertRaises(LLMServiceError) as ctx:
            self.service.structured_output([], SampleOutput)
        assert "Messages cannot be empty" in str(ctx.exception)
