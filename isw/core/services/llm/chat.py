import json
from typing import Any, Dict, Generator, Iterable, List, Optional, Union
from uuid import uuid4

from litellm import Router
from litellm._logging import _disable_debugging
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from tenacity import retry, stop_after_attempt, wait_exponential
from vaul import StructuredOutput, Toolkit

from isw.core.services.llm.base import LLMClient
from isw.shared.config import config
from isw.shared.logging.logger import logger

# Debugging is extremely verbose and makes terminal unusable when testing
_disable_debugging()


class ChatClient(LLMClient):
    """
    Simplified client for chat completions via LiteLLM with unified batch,
    streaming, and tool-call execution using the Vercel AI SDK data-stream protocol.
    """

    def __init__(
        self,
        models: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        names = models or config().chat_models
        validated = self.validate_models(names, model_type="chat")
        self.primary = validated[0]
        router_conf = self._build_router_config(validated)
        self.router = Router(**router_conf)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        tools: Optional[Toolkit] = None,
        max_steps: Optional[int] = None,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], Generator[str, None, None]]:
        params = self._build_params(messages, stream, tools, **kwargs)
        native = self._send_request(params)
        if stream:
            return self.stream(native, tools, max_steps=max_steps, messages=messages.copy())
        return self.batch(native, tools, messages=messages, max_steps=max_steps)

    def batch(
        self,
        response: ChatCompletion,
        tools: Toolkit,
        messages: Optional[List[Dict[str, Any]]] = None,
        max_steps: Optional[int] = None,
        step: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Process a chat completion response in batch mode, handling tool calls and recursion.

        Args:
            response: The ChatCompletion response from the model
            tools: Toolkit instance containing available tools
            messages: Optional conversation messages for context
            max_steps: Optional maximum number of steps for the chat completion
            step: Current step number in the conversation

        Returns:
            List of message dictionaries containing assistant responses and tool results
        """
        if max_steps and step >= max_steps:
            logger.warning(
                "Maximum allowed steps reached (step: %d, max_steps: %d). Aborting further recursion.",
                step,
                max_steps,
            )
            return [
                {
                    "role": "assistant",
                    "content": "I've reached my step limit. Please continue the conversation if needed.",
                    "finish_reason": "continue_prompt",
                }
            ]

        results: List[Dict[str, Any]] = []
        choice = response.choices[0]
        tool_messages = []
        messages = messages or []

        # Add the assistant message to the results
        assistant_message = {
            "role": "assistant",
            "content": choice.message.content,
            "finish_reason": choice.finish_reason,
        }

        # Handle tool calls
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_calls_data = []
            for tc in choice.message.tool_calls:
                tool_calls_data.append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )

            # Add the tool calls to the assistant message
            assistant_message["tool_calls"] = tool_calls_data

        # Run the tool calls
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                    logger.info(f"Running tool: {tc.function.name}")
                    out = tools.run_tool(tc.function.name, args)
                except Exception as e:
                    out = {
                        "error": str(e),
                        "tool": tc.function.name,
                        "arguments": tc.function.arguments,
                    }

                tool_message = {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(out),
                }
                tool_messages.append(tool_message)

        # Add the assistant message to the results
        results.append(assistant_message)

        # Add the tool messages to the results
        results.extend(tool_messages)

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            next_messages = messages + [
                assistant_message,
                *tool_messages,
            ]

            next_response = self._send_request(self._build_params(next_messages, False, tools))
            next_results = self.batch(next_response, tools, next_messages, max_steps=max_steps, step=step + 1)
            results.extend(next_results)

        return results

    def stream(
        self,
        chunks: Iterable[ChatCompletionChunk],
        tools: Toolkit,
        max_steps: Optional[int] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        step: int = 0,
    ) -> Generator[str, None, None]:
        """
        Stream responses and handle tool calls according to the Vercel AI SDK data-stream protocol.

        Args:
            chunks: Iterable of chat completion chunks from the model
            tools: Toolkit instance containing available tools
            max_steps: Optional maximum number of steps for the chat completion
            messages: Optional conversation messages for context
            step: Current step number in the conversation

        Yields:
            String chunks following the Vercel AI SDK data-stream protocol
        """
        if max_steps and step >= max_steps:
            logger.warning(
                "Maximum allowed steps reached (step: %d, max_steps: %d). Aborting further recursion.",
                step,
                max_steps,
            )
            yield '2:[{"type":"continue_prompt"}]\n'
            yield 'd:{"finishReason":"continue_prompt"}\n'
            return

        messages = messages or []
        message_id = uuid4().hex
        yield f'f:{{"messageId":"{message_id}"}}\n'

        draft_calls: List[Dict[str, Any]] = []
        draft_index = -1
        prompt_tokens = completion_tokens = 0

        # first pass – build up tool calls
        for chunk in chunks:
            if hasattr(chunk, "usage"):
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens

            for choice in chunk.choices:
                delta = getattr(choice, "delta", None)

                # build up tool-calls
                if delta and getattr(delta, "tool_calls", None):
                    for tc in delta.tool_calls:
                        if tc.id is not None:  # new call
                            draft_index += 1
                            draft_calls.append(
                                {
                                    "id": tc.id,
                                    "name": tc.function.name or "",
                                    "arguments": "",
                                }
                            )
                            yield f'b:{{"toolCallId":"{tc.id}","toolName":"{tc.function.name or ""}"}}\n'
                        else:  # argument chunk
                            call = draft_calls[draft_index]
                            if tc.function.arguments:
                                call["arguments"] += tc.function.arguments
                                yield (
                                    f'c:{{"toolCallId":"{call["id"]}",'
                                    f'"argsTextDelta":{json.dumps(tc.function.arguments)}}}\n'
                                )

                # normal text delta
                if delta and getattr(delta, "content", None):
                    yield f"0:{json.dumps(delta.content)}\n"

                # anthropic reasoning delta (optional)
                if delta and getattr(delta, "system_reasoning", None):
                    yield f"g:{json.dumps(delta.system_reasoning)}\n"

                # stop handled after loop

        # if we have tool calls, we need to run them
        if draft_calls:
            tool_messages: List[Dict[str, Any]] = []

            for call in draft_calls:
                # run tool
                try:
                    result = tools.run_tool(call["name"], json.loads(call["arguments"]))
                except Exception as e:
                    result = {"error": str(e)}

                yield f'a:{{"toolCallId":"{call["id"]}","result":{json.dumps(result)}}}\n'

                # collect <tool> message for second pass
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(result),
                    }
                )

            # partial close, signal continuation
            yield (
                f'e:{{"finishReason":"tool-calls","isContinued":true,'
                f'"usage":{{"promptTokens":{prompt_tokens},'
                f'"completionTokens":{completion_tokens}}}}}\n'
            )

            # build prompt for second pass
            next_messages = messages + [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {
                                "name": c["name"],
                                "arguments": c["arguments"],
                            },
                        }
                        for c in draft_calls
                    ],
                    "content": None,
                },
                *tool_messages,
            ]

            # second completion (recursive stream)
            next_chunks = self._send_request(self._build_params(next_messages, True, tools))
            yield from self.stream(
                next_chunks,
                tools,
                max_steps=max_steps,
                messages=next_messages,
                step=step + 1,
            )
            return  # prevent normal close below

        yield (
            f'd:{{"finishReason":"stop","usage":{{"promptTokens":{prompt_tokens},'
            f'"completionTokens":{completion_tokens}}}}}\n'
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=8),
        reraise=True,
    )
    def structured_output(
        self,
        messages: List[Dict[str, Any]],
        structured_output: StructuredOutput,
        **kwargs,
    ) -> Any:
        if not messages:
            raise ValueError("Messages list cannot be empty")
        schema = structured_output.tool_call_schema
        params = self._build_params(
            messages,
            False,
            tools=[{"type": "function", "function": schema}],
            tool_choice={"type": "function", "function": {"name": schema["name"]}},
            **kwargs,
        )
        resp = self._send_request(params)
        try:
            return structured_output.from_response(resp)
        except Exception as e:
            logger.exception("Structured output failed: %s", e)
            raise ValueError(f"Structured output error: {e}") from e

    def _build_params(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        tools: Optional[Toolkit] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": self.primary["key"],
            "messages": messages,
            "stream": stream,
        }
        if tools:
            if isinstance(tools, Toolkit) and tools.has_tools():
                params["tools"] = tools.tool_schemas()
            elif isinstance(tools, list):
                params["tools"] = tools
            else:
                raise ValueError("Tools must be a Toolkit or a list of tool schemas")

        params.update(extra)
        return params

    def _send_request(self, params: Dict[str, Any]) -> Any:
        try:
            return self.router.completion(
                metadata=self._get_metadata(),
                **params,
            )
        except Exception as e:
            logger.error("Chat completion failed: %s", e, exc_info=True)
            raise
