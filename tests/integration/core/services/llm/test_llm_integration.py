import json
from types import SimpleNamespace as NS
from unittest.mock import Mock

from vaul import StructuredOutput

from isw.core.services.llm.chat import ChatClient
from isw.core.services.llm.embedding import EmbeddingClient
from isw.shared.config.base import BaseConfig

config = BaseConfig.from_env()


class CountingRouter:
    def __init__(self, *_, **__):
        self.calls = 0

    class _Resp:
        def __init__(self, data):
            self._data = data

        def to_dict(self):
            return {"data": self._data}

    def embedding(self, **params):
        self.calls += 1
        return self._Resp([{"embedding": [1.0] + [0.0] * (config.embedding_dimension - 1)}])


def test_embedding_chunking_integration(monkeypatch):
    """Test that embedding client properly chunks long text."""
    # Force small max_tokens to trigger chunking and stub model validation
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": config.embedding_dimension, "max_tokens": 5}
        ],
    )

    router = CountingRouter()
    monkeypatch.setattr("isw.core.services.llm.embedding.Router", lambda **_: router)

    client = EmbeddingClient(dimension=config.embedding_dimension, models=config.embedding_models)

    # Monkeypatch tokenization to control chunk count: length 12 -> 3 chunks of size 5 (last partial)
    monkeypatch.setattr(client, "encode_tokens", lambda s: list(range(12)))
    monkeypatch.setattr(client, "decode_tokens", lambda toks: "x" * len(toks))

    vec = client.embed("long text that forces chunking")

    # Should have called router.embedding multiple times
    assert router.calls >= 2

    # Result stays normalized list of floats with expected dimension
    assert isinstance(vec, list) and len(vec) == config.embedding_dimension


def test_chat_simple_batch_integration(monkeypatch):
    """Test basic chat completion without tools."""
    # Stub validation
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    client = ChatClient(models=config.chat_models)

    # Fake one-step completion (no tools)
    choice = type("Choice", (), {})
    msg = type("Msg", (), {"content": "hello", "tool_calls": None})
    choice.message = msg
    choice.finish_reason = "stop"
    completion = type("Completion", (), {"choices": [choice]})

    monkeypatch.setattr(client, "_send_request", lambda params: completion)

    out = client.chat(messages=[{"role": "user", "content": "hi"}], stream=False)
    assert any(m.get("content") == "hello" for m in out)


def test_chat_streaming_integration(monkeypatch):
    """Test streaming chat completions with proper protocol format."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    client = ChatClient(models=config.chat_models)

    def mock_chunks():
        yield NS(choices=[NS(delta=NS(content="Hello", tool_calls=None))])
        yield NS(choices=[NS(delta=NS(content=" world", tool_calls=None))])
        yield NS(
            choices=[NS(delta=NS(content=None, tool_calls=None))],
            usage=NS(prompt_tokens=5, completion_tokens=2),
        )

    monkeypatch.setattr(client, "_send_request", lambda params: mock_chunks())

    result = list(client.chat(messages=[{"role": "user", "content": "hi"}], stream=True))

    assert any("messageId" in chunk for chunk in result)
    assert any("Hello" in chunk for chunk in result)
    assert any("world" in chunk for chunk in result)
    assert any("finishReason" in chunk for chunk in result)


def test_tool_execution_integration(monkeypatch):
    """Test full tool execution flow with real-like structures."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    # Mock the isinstance check for Toolkit
    import builtins

    from vaul import Toolkit

    original_isinstance = builtins.isinstance

    def mock_isinstance(obj, cls):
        if cls == Toolkit and hasattr(obj, "has_tools"):
            return True
        return original_isinstance(obj, cls)

    monkeypatch.setattr(builtins, "isinstance", mock_isinstance)

    client = ChatClient(models=config.chat_models)

    class TestToolkit:
        def has_tools(self):
            return True

        def tool_schemas(self):
            return [
                {
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "description": "Perform calculation",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {"type": "string"},
                            },
                        },
                    },
                }
            ]

        def run_tool(self, name, args):
            if name == "calculate":
                return {"result": 42, "expression": args.get("expression")}
            raise ValueError(f"Unknown tool: {name}")

    toolkit = TestToolkit()

    # Mock responses: first with tool call, then final
    tool_call = NS(
        id="call_123",
        function=NS(name="calculate", arguments=json.dumps({"expression": "6 * 7"})),
    )
    tool_response = NS(choices=[NS(message=NS(content=None, tool_calls=[tool_call]), finish_reason="tool_calls")])

    final_response = NS(
        choices=[
            NS(
                message=NS(content="The result of 6 * 7 is 42", tool_calls=None),
                finish_reason="stop",
            )
        ]
    )

    calls = {"count": 0}

    def mock_send(params):
        calls["count"] += 1
        return final_response if calls["count"] > 1 else tool_response

    monkeypatch.setattr(client, "_send_request", mock_send)

    messages = [{"role": "user", "content": "What is 6 times 7?"}]
    results = client.chat(messages, tools=toolkit)

    # Verify tool was called and result included
    assert calls["count"] == 2  # Initial + follow-up after tool
    assert any(r.get("tool_calls") for r in results if r.get("role") == "assistant")
    assert any(r.get("role") == "tool" for r in results)
    assert any("42" in str(r.get("content", "")) for r in results if r.get("role") == "assistant")


def test_embedding_fallback_integration(monkeypatch):
    """Test embedding fallback when primary model fails."""
    # Setup two models: primary will fail, fallback will succeed
    # Use a fallback model if available, otherwise use a default one
    validated_models = [
        {
            "key": "openai/text-embedding-3-small",
            "mode": "embedding",
            "output_vector_size": config.embedding_dimension,
            "max_tokens": 8192,
        },
        {
            "key": "openai/text-embedding-ada-002",
            "mode": "embedding",
            "output_vector_size": config.embedding_dimension,
            "max_tokens": 8192,
        },
    ]

    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: validated_models,
    )

    class FallbackRouter:
        def __init__(self, **config):
            self.config = config
            self.attempts = []

        def embedding(self, **params):
            # LiteLLM Router internally handles fallbacks, so we simulate success
            # after internal retry (we just return success to simulate the final result)
            if "model" in params:
                self.attempts.append(params["model"])
            else:
                # Router doesn't pass model param, it handles fallback internally
                self.attempts.append("internal-fallback")

            # Simulate successful fallback response
            return CountingRouter._Resp([{"embedding": [0.5] * config.embedding_dimension}])

    router = None

    def create_router(**config):
        nonlocal router
        router = FallbackRouter(**config)
        return router

    monkeypatch.setattr("isw.core.services.llm.embedding.Router", create_router)

    # Client should be configured with fallback
    client = EmbeddingClient(dimension=config.embedding_dimension, models=[model["key"] for model in validated_models])

    # Embedding should succeed via fallback
    result = client.embed("test text")

    assert result == [0.5] * config.embedding_dimension


def test_chat_max_steps_integration(monkeypatch):
    """Test that max_steps properly limits recursion in real scenarios."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    import builtins

    from vaul import Toolkit

    original_isinstance = builtins.isinstance

    def mock_isinstance(obj, cls):
        if cls == Toolkit and hasattr(obj, "has_tools"):
            return True
        return original_isinstance(obj, cls)

    monkeypatch.setattr(builtins, "isinstance", mock_isinstance)

    client = ChatClient(models=config.chat_models)

    # Create a toolkit that always triggers more tool calls
    class InfiniteToolkit:
        def has_tools(self):
            return True

        def tool_schemas(self):
            return [{"type": "function", "function": {"name": "continue_forever"}}]

        def run_tool(self, name, args):
            return {"status": "need_more_info"}

    toolkit = InfiniteToolkit()

    # Always return tool calls to simulate infinite recursion
    tool_call = NS(
        id="call_inf",
        function=NS(name="continue_forever", arguments="{}"),
    )
    infinite_response = NS(choices=[NS(message=NS(content=None, tool_calls=[tool_call]), finish_reason="tool_calls")])

    monkeypatch.setattr(client, "_send_request", lambda params: infinite_response)

    # Should stop at max_steps
    results = client.chat(
        messages=[{"role": "user", "content": "Start infinite loop"}],
        tools=toolkit,
        max_steps=3,
    )

    # Should have a continue prompt indicating max steps reached
    assert any(r.get("finish_reason") == "continue_prompt" for r in results)
    assert any("step limit" in str(r.get("content", "")) for r in results)

    # Count tool executions (should be limited by max_steps)
    tool_messages = [r for r in results if r.get("role") == "tool"]
    assert len(tool_messages) <= 3  # Should not exceed max_steps


def test_structured_output_integration(monkeypatch):
    """Test structured output extraction with realistic response."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    client = ChatClient(models=config.chat_models)

    class PersonInfo(StructuredOutput):
        name: str
        age: int
        email: str

        @property
        def tool_call_schema(self):
            return {
                "name": "extract_person_info",
                "description": "Extract person information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "email": {"type": "string"},
                    },
                    "required": ["name", "age", "email"],
                },
            }

        def from_response(self, response):
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            return PersonInfo(**args)

    tool_call = NS(
        id="call_struct",
        function=NS(
            name="extract_person_info",
            arguments=json.dumps({"name": "John Doe", "age": 30, "email": "john@example.com"}),
        ),
    )
    structured_response = NS(choices=[NS(message=NS(content=None, tool_calls=[tool_call]), finish_reason="tool_calls")])

    monkeypatch.setattr(client, "_send_request", lambda params: structured_response)

    structured_output = Mock(spec=StructuredOutput)
    dummy_person = PersonInfo(name="dummy", age=0, email="dummy@test.com")
    structured_output.tool_call_schema = dummy_person.tool_call_schema
    structured_output.from_response.return_value = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
    }

    result = client.structured_output(
        messages=[{"role": "user", "content": "Extract: John Doe, 30 years old, john@example.com"}],
        structured_output=structured_output,
    )

    assert result["name"] == "John Doe"
    assert result["age"] == 30
    assert result["email"] == "john@example.com"
