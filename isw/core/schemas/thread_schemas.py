import json
from typing import Dict, List

from marshmallow import Schema, fields, post_load

from .utils import is_between


def map_to_openai_schema(messages: List[Dict]) -> List[Dict]:
    """Convert client messages to OpenAI-compatible format."""

    openai_messages = []

    for message in messages:
        role = message.get("role")
        parts = message.get("parts", [])
        content = ""

        if parts:
            valid_parts = [part for part in parts if part.get("type") == "text" and part.get("text")]
            content = "\n".join(p["text"] for p in valid_parts) if valid_parts else ""
        elif message.get("content"):
            content = message["content"]

        tool_calls = []

        if "toolInvocations" in message:
            for invocation in message["toolInvocations"]:
                args = invocation.get("args", {})
                if isinstance(args, dict):
                    args = json.dumps(args)

                tool_calls.append(
                    {
                        "id": invocation["toolCallId"],
                        "type": "function",
                        "function": {
                            "name": invocation["toolName"],
                            "arguments": args,
                        },
                    }
                )

        openai_message = {
            "role": role,
            "content": content if role in ("user", "assistant", "system") else None,
        }

        if tool_calls:
            openai_message["tool_calls"] = tool_calls

        openai_messages.append(openai_message)

        if "toolInvocations" in message:
            for invocation in message["toolInvocations"]:
                if invocation.get("result") is not None:
                    result = invocation["result"]
                    if not isinstance(result, str):
                        result = json.dumps(result)

                    openai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": invocation["toolCallId"],
                            "content": result,
                        }
                    )

    return openai_messages


class ChatMessagesSchema(Schema):
    max_steps = fields.Int(required=False, validate=is_between(1, 100), allow_none=True)
    messages = fields.List(fields.Dict(), required=True)
    model = fields.Str(required=False, allow_none=True)
    stream = fields.Bool(required=False)

    @post_load
    def map_messages(self, data: dict, **kwargs):
        return {
            "messages": map_to_openai_schema(data.get("messages")),
            "model": data.get("model"),
            "max_steps": int(data.get("max_steps", 10)),
            "stream": data.get("stream", True),
        }


chat_messages_schema = ChatMessagesSchema()
