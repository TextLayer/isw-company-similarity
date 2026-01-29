import unittest
from unittest.mock import MagicMock, patch

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


class TestStructuredOutput(unittest.TestCase):
    def setUp(self):
        self.service = LLMService()

    def test_raises_for_empty_messages(self):
        with self.assertRaises(LLMServiceError) as ctx:
            self.service.structured_output([], SampleOutput)
        assert "Messages cannot be empty" in str(ctx.exception)

    @patch("isw.core.services.llm.service.completion")
    def test_returns_parsed_output(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"name": "test", "value": 42}'
        mock_completion.return_value = mock_response

        result = self.service.structured_output(
            messages=[{"role": "user", "content": "test prompt"}],
            output_structure=SampleOutput,
        )

        assert isinstance(result, SampleOutput)
        assert result.name == "test"
        assert result.value == 42

    @patch("isw.core.services.llm.service.completion")
    def test_calls_completion_with_correct_args(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"name": "test", "value": 1}'
        mock_completion.return_value = mock_response

        messages = [{"role": "user", "content": "extract info"}]
        self.service.structured_output(messages, SampleOutput)

        mock_completion.assert_called_once_with(
            model="gpt-4o-mini",
            messages=messages,
            response_format=SampleOutput,
        )

    @patch("isw.core.services.llm.service.completion")
    def test_raises_on_api_error(self, mock_completion):
        mock_completion.side_effect = Exception("API error")

        with self.assertRaises(LLMServiceError) as ctx:
            self.service.structured_output(
                messages=[{"role": "user", "content": "test"}],
                output_structure=SampleOutput,
            )
        assert "Failed to generate structured output" in str(ctx.exception)

    @patch("isw.core.services.llm.service.completion")
    def test_raises_on_invalid_json(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json"
        mock_completion.return_value = mock_response

        with self.assertRaises(LLMServiceError):
            self.service.structured_output(
                messages=[{"role": "user", "content": "test"}],
                output_structure=SampleOutput,
            )

    @patch("isw.core.services.llm.service.completion")
    def test_raises_on_missing_required_field(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"name": "test"}'  # Missing 'value'
        mock_completion.return_value = mock_response

        with self.assertRaises(LLMServiceError):
            self.service.structured_output(
                messages=[{"role": "user", "content": "test"}],
                output_structure=SampleOutput,
            )
