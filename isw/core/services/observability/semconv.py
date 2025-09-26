from typing import Any

GENAI = {
    # Request
    "system": "gen_ai.system",
    "op_name": "gen_ai.operation.name",
    "req_model": "gen_ai.request.model",
    "req_temperature": "gen_ai.request.temperature",
    "req_top_p": "gen_ai.request.top_p",
    "req_max_tokens": "gen_ai.request.max_tokens",
    "req_stream": "gen_ai.request.stream",
    # Prompts / messages
    "prompt_role": "gen_ai.prompt.{i}.role",
    "prompt_content": "gen_ai.prompt.{i}.content",
    # Response
    "res_model": "gen_ai.response.model",
    "res_id": "gen_ai.response.id",
    "res_finish_reasons": "gen_ai.response.finish_reasons",
    "res_fingerprint": "gen_ai.response.system_fingerprint",
    # Completions
    "comp_role": "gen_ai.completion.{i}.role",
    "comp_content": "gen_ai.completion.{i}.content",
    # Usage
    "usage_prompt": "gen_ai.usage.prompt_tokens",
    "usage_completion": "gen_ai.usage.completion_tokens",
    "usage_total": "gen_ai.usage.total_tokens",
}

ERR = {
    "flag": "error",
    "type": "error.type",
    "message": "error.message",
}

CUSTOM = {
    "total_cost": "llm.usage.total_cost",
    "cache_hit": "llm.cache_hit",
}


def set_kv(span, key: str, value: Any) -> None:
    if value is None:
        return
    try:
        span.set_attribute(key, value)
    except Exception:
        span.set_attribute(key, str(value))
