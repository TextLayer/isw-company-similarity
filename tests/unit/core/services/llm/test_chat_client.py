import json
from types import SimpleNamespace as NS
from unittest.mock import Mock

from isw.core.services.llm.chat import ChatClient


class DummyToolkit:
    def __init__(self):
        self._calls = []

    def has_tools(self):
        return True

    def tool_schemas(self):
        return [{"type": "function", "function": {"name": "get_weather"}}]

    def run_tool(self, name, args):
        self._calls.append((name, args))
        return {"weather": "sunny", "city": args.get("city")}


def _chat_completion_tool_call():
    tool_call = NS(id="call1", function=NS(name="get_weather", arguments=json.dumps({"city": "SF"})))
    choice = NS(message=NS(content=None, tool_calls=[tool_call]), finish_reason="tool_calls")
    return NS(choices=[choice])


def _chat_completion_final():
    choice = NS(message=NS(content="It is sunny in SF", tool_calls=None), finish_reason="stop")
    return NS(choices=[choice])


def test_batch_tool_call_recursion(monkeypatch):
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    calls = {"i": 0}

    def fake_send(params):
        if calls["i"] == 0:
            calls["i"] += 1
            return _chat_completion_tool_call()
        return _chat_completion_final()

    monkeypatch.setattr(client, "_send_request", fake_send)

    toolkit = DummyToolkit()

    original_build_params = client._build_params

    def patched_build_params(messages, stream=False, tools=None, **extra):
        if tools and hasattr(tools, "has_tools"):
            return original_build_params(messages, stream, tools.tool_schemas() if tools.has_tools() else None, **extra)
        return original_build_params(messages, stream, tools, **extra)

    monkeypatch.setattr(client, "_build_params", patched_build_params)

    results = client.batch(_chat_completion_tool_call(), toolkit, messages=[{"role": "user", "content": "Hi"}])

    assert any(r.get("tool_calls") for r in results if r.get("role") == "assistant")
    assert any(r.get("role") == "tool" for r in results)
    assert any(r.get("content") == "It is sunny in SF" for r in results if r.get("role") == "assistant")


def test_batch_max_steps_limit(monkeypatch):
    """Test that batch respects max_steps limit and doesn't recurse infinitely."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    monkeypatch.setattr(client, "_send_request", lambda _: _chat_completion_tool_call())

    toolkit = DummyToolkit()

    original_build_params = client._build_params

    def patched_build_params(messages, stream=False, tools=None, **extra):
        if tools and hasattr(tools, "has_tools"):
            return original_build_params(messages, stream, tools.tool_schemas() if tools.has_tools() else None, **extra)
        return original_build_params(messages, stream, tools, **extra)

    monkeypatch.setattr(client, "_build_params", patched_build_params)

    results = client.batch(
        _chat_completion_tool_call(),
        toolkit,
        messages=[{"role": "user", "content": "Hi"}],
        max_steps=2,
    )

    assert any(r.get("finish_reason") == "continue_prompt" for r in results)
    assert any("step limit" in str(r.get("content", "")) for r in results)


def test_stream_basic_text(monkeypatch):
    """Test streaming basic text responses without tools."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    def mock_chunks():
        yield NS(choices=[NS(delta=NS(content="Hello ", tool_calls=None))])
        yield NS(choices=[NS(delta=NS(content="world!", tool_calls=None))])
        yield NS(
            choices=[NS(delta=NS(content=None, tool_calls=None))],
            usage=NS(prompt_tokens=10, completion_tokens=5),
        )

    toolkit = Mock()
    toolkit.has_tools.return_value = False

    result = list(client.stream(mock_chunks(), toolkit))

    # Check for text chunks and proper closing
    assert any('"Hello "' in chunk for chunk in result)
    assert any('"world!"' in chunk for chunk in result)
    assert any('"finishReason":"stop"' in chunk for chunk in result)


def test_stream_with_tool_calls(monkeypatch):
    """Test streaming with tool call handling."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    # Mock Router to avoid real initialization
    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    def mock_chunks():
        yield NS(
            choices=[
                NS(
                    delta=NS(
                        content=None,
                        tool_calls=[NS(id="tc1", function=NS(name="get_weather", arguments=None))],
                    )
                )
            ]
        )
        yield NS(
            choices=[
                NS(
                    delta=NS(
                        content=None,
                        tool_calls=[NS(id=None, function=NS(name=None, arguments='{"city":'))],
                    )
                )
            ]
        )
        yield NS(
            choices=[
                NS(
                    delta=NS(
                        content=None,
                        tool_calls=[NS(id=None, function=NS(name=None, arguments='"SF"}'))],
                    )
                )
            ]
        )

    def mock_final_chunks():
        yield NS(choices=[NS(delta=NS(content="It is sunny in SF", tool_calls=None))])

    toolkit = DummyToolkit()

    original_build_params = client._build_params

    def patched_build_params(messages, stream=False, tools=None, **extra):
        if tools and hasattr(tools, "has_tools"):
            return original_build_params(messages, stream, tools.tool_schemas() if tools.has_tools() else None, **extra)
        return original_build_params(messages, stream, tools, **extra)

    monkeypatch.setattr(client, "_build_params", patched_build_params)

    call_count = {"count": 0}

    def mock_send_request(params):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return mock_final_chunks()
        return []

    monkeypatch.setattr(client, "_send_request", mock_send_request)

    result = list(client.stream(mock_chunks(), toolkit))

    assert any('"toolName":"get_weather"' in chunk for chunk in result)
    assert any('"argsTextDelta"' in chunk for chunk in result)
    assert any('"It is sunny in SF"' in chunk for chunk in result)


def test_structured_output(monkeypatch):
    """Test structured output functionality."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    mock_structured = Mock()
    mock_structured.tool_call_schema = {
        "name": "extract_info",
        "description": "Extract information",
    }

    tool_call = NS(
        id="call1",
        function=NS(name="extract_info", arguments=json.dumps({"name": "John", "age": 30})),
    )
    choice = NS(message=NS(content=None, tool_calls=[tool_call]), finish_reason="tool_calls")
    mock_response = NS(choices=[choice])

    monkeypatch.setattr(client, "_send_request", lambda _: mock_response)
    mock_structured.from_response.return_value = {"name": "John", "age": 30}

    messages = [{"role": "user", "content": "Extract info from text"}]
    result = client.structured_output(messages, mock_structured)

    assert result == {"name": "John", "age": 30}
    mock_structured.from_response.assert_called_once_with(mock_response)


def test_chat_interface_with_stream_flag(monkeypatch):
    """Test the main chat interface with stream flag."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    monkeypatch.setattr(client, "_send_request", lambda _: _chat_completion_final())
    result = client.chat([{"role": "user", "content": "Hi"}], stream=False)
    assert isinstance(result, list)

    def mock_chunks():
        yield NS(choices=[NS(delta=NS(content="Hi", tool_calls=None))])

    monkeypatch.setattr(client, "_send_request", lambda _: mock_chunks())
    result = client.chat([{"role": "user", "content": "Hi"}], stream=True)

    assert hasattr(result, "__next__")


def test_error_handling_in_tool_execution(monkeypatch):
    """Test error handling when tool execution fails."""
    monkeypatch.setattr(
        ChatClient,
        "validate_models",
        lambda self, names, model_type: [{"key": names[0], "mode": "chat"}],
    )

    mock_router = Mock()
    monkeypatch.setattr("textlayer.core.services.llm.chat.Router", lambda **_: mock_router)

    client = ChatClient(models=["test-chat-model"])

    class ErrorToolkit:
        def has_tools(self):
            return True

        def tool_schemas(self):
            return [{"type": "function", "function": {"name": "failing_tool"}}]

        def run_tool(self, name, args):
            raise RuntimeError("Tool execution failed")

    toolkit = ErrorToolkit()

    original_build_params = client._build_params

    def patched_build_params(messages, stream=False, tools=None, **extra):
        if tools and hasattr(tools, "has_tools"):
            return original_build_params(messages, stream, tools.tool_schemas() if tools.has_tools() else None, **extra)
        return original_build_params(messages, stream, tools, **extra)

    monkeypatch.setattr(client, "_build_params", patched_build_params)

    tool_call = NS(
        id="call1",
        function=NS(name="failing_tool", arguments=json.dumps({"param": "value"})),
    )
    choice = NS(message=NS(content=None, tool_calls=[tool_call]), finish_reason="tool_calls")
    tool_response = NS(choices=[choice])

    final_choice = NS(message=NS(content="Tool failed but continuing", tool_calls=None), finish_reason="stop")
    final_response = NS(choices=[final_choice])

    call_count = {"count": 0}

    def mock_send(params):
        call_count["count"] += 1
        return final_response if call_count["count"] > 1 else tool_response

    monkeypatch.setattr(client, "_send_request", mock_send)

    results = client.batch(tool_response, toolkit)

    tool_messages = [r for r in results if r.get("role") == "tool"]
    assert len(tool_messages) > 0
    error_content = json.loads(tool_messages[0]["content"])
    assert "error" in error_content
    assert "Tool execution failed" in error_content["error"]
