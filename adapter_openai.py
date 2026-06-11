"""OpenAI adapter for the Chapter 7 agent loop.

Only two seams change across providers (Chapter 7, Cross-Model Notes):
extracting tool calls from a response and formatting tool results for the
next request. Swap these two functions in for the Anthropic versions; the
while-loop architecture is unchanged.

Shapes follow OpenAI's Chat Completions API: the model signals tool use with
finish_reason "tool_calls", arguments arrive as a JSON string, and results
go back as role="tool" messages keyed by tool_call_id.
"""

import json


def is_tool_use(response) -> bool:
    return response.choices[0].finish_reason == "tool_calls"


def extract_tool_calls(response) -> list[dict]:
    """Normalize a chat completion into [{id, name, input}, ...]."""
    message = response.choices[0].message
    calls = []
    for tc in message.tool_calls or []:
        calls.append({
            "id": tc.id,
            "name": tc.function.name,
            "input": json.loads(tc.function.arguments),  # arrives as a string
        })
    return calls


def format_tool_results(results: list[dict]) -> list[dict]:
    """[{id, content}, ...] -> one role="tool" message per result."""
    return [
        {"role": "tool", "tool_call_id": r["id"], "content": r["content"]}
        for r in results
    ]
