"""Gemini adapter for the Chapter 7 agent loop.

Gemini returns function_call parts inside the response content and takes
results back as function_response parts in a user turn. finish_reason does
not distinguish a tool request from a final answer (Chapter 7, Cross-Model
Notes), so is_tool_use inspects the parts.
"""


def is_tool_use(response) -> bool:
    parts = response.candidates[0].content.parts or []
    return any(getattr(p, "function_call", None) is not None for p in parts)


def extract_tool_calls(response) -> list[dict]:
    """Normalize a generate_content response into [{id, name, input}, ...]."""
    calls = []
    for part in response.candidates[0].content.parts or []:
        fc = getattr(part, "function_call", None)
        if fc is not None:
            calls.append({
                "id": getattr(fc, "id", None),  # present on recent models
                "name": fc.name,
                "input": dict(fc.args or {}),
            })
    return calls


def format_tool_results(results: list[dict]) -> list[dict]:
    """[{name, content, id}, ...] -> function_response parts for one user turn.

    Gemini matches responses to calls by name (and id when the model
    provided one), so each result must carry the originating tool name.
    """
    parts = []
    for r in results:
        fr = {"name": r["name"], "response": {"result": r["content"]}}
        if r.get("id"):
            fr["id"] = r["id"]
        parts.append({"function_response": fr})
    return parts
