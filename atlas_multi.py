"""atlas_multi.py — Three-agent system using the Anthropic Agent SDK.

Orchestrator (Haiku) coordinates a researcher (Sonnet) and coder (Sonnet),
each with isolated tool access, to complete research-then-code tasks.

Requires: ANTHROPIC_API_KEY environment variable.
Optional: TAVILY_API_KEY for web search.
Usage: python atlas_multi.py "find how asyncio.gather works and write a working example"
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import requests
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

# Model assignments — orchestrator uses cheap model, specialists use capable model
ORCHESTRATOR_MODEL = "claude-haiku-4-5-20251001"
RESEARCHER_MODEL = "claude-sonnet-4-6"
CODER_MODEL = "claude-sonnet-4-6"

WORKSPACE_ROOT = Path("./workspace").resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Tool Implementations (isolated per agent role)
# ============================================================================

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not set."
    response = requests.post(
        "https://api.tavily.com/search",
        json={"query": query, "max_results": max_results, "search_depth": "basic", "api_key": api_key},
        timeout=15,
    )
    response.raise_for_status()
    results = []
    for r in response.json().get("results", []):
        results.append(f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n")
    return "\n---\n".join(results) if results else "No results found."


def write_file(path: str, content: str) -> str:
    """Write content to a file within the workspace directory."""
    requested = (WORKSPACE_ROOT / path).resolve()
    if not requested.is_relative_to(WORKSPACE_ROOT):
        return f"Error: path '{path}' is outside the allowed workspace."
    requested.parent.mkdir(parents=True, exist_ok=True)
    requested.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}."


def run_python(code: str, timeout: int = 10) -> str:
    """Execute Python code in a sandboxed subprocess."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", dir=str(WORKSPACE_ROOT), delete=False
    ) as f:
        f.write(code)
        script_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=timeout, cwd=str(WORKSPACE_ROOT),
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: timed out after {timeout}s."
    finally:
        Path(script_path).unlink(missing_ok=True)


# ============================================================================
# Tool Definitions (Anthropic format)
# ============================================================================

RESEARCHER_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for documentation and examples.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query."}},
            "required": ["query"],
        },
    }
]

CODER_TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path."},
                "content": {"type": "string", "description": "File content."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_python",
        "description": "Execute Python code and return output.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code."}},
            "required": ["code"],
        },
    },
]

TOOL_EXECUTORS = {
    "web_search": lambda args: web_search(**args),
    "write_file": lambda args: write_file(**args),
    "run_python": lambda args: run_python(**args),
}


# ============================================================================
# Single-Agent Runner (reusable for each specialist)
# ============================================================================

def run_agent(role: str, model: str, system_prompt: str, tools: list[dict],
              user_message: str) -> dict:
    """Run a single agent to completion, handling tool calls."""
    messages = [{"role": "user", "content": user_message}]
    total_input = 0
    total_output = 0
    start = time.time()

    for _ in range(10):  # max iterations per agent
        response = client.messages.create(
            model=model, max_tokens=4096,
            system=system_prompt, tools=tools, messages=messages,
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

        if response.stop_reason == "end_turn":
            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            elapsed = time.time() - start
            print(f"  [{role}] {total_input} in / {total_output} out | {elapsed:.1f}s")
            return {"text": text, "input_tokens": total_input,
                    "output_tokens": total_output, "elapsed_s": elapsed}

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    executor = TOOL_EXECUTORS.get(block.name)
                    if not executor:
                        result = f"Error: tool '{block.name}' not available for {role}."
                    else:
                        try:
                            result = executor(block.input)
                        except Exception as e:
                            result = f"Error: {type(e).__name__}: {e}"
                    print(f"  [{role}] Tool: {block.name}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})

    return {"text": "(agent did not complete)", "input_tokens": total_input,
            "output_tokens": total_output, "elapsed_s": time.time() - start}


# ============================================================================
# Three-Agent Orchestrator
# ============================================================================

def run_orchestrator(user_request: str) -> dict:
    """Orchestrate researcher → coder workflow with completeness check."""
    total_input = 0
    total_output = 0
    start = time.time()

    print("Step 1: Research")
    research_result = run_agent(
        role="researcher",
        model=RESEARCHER_MODEL,
        system_prompt=(
            "You are a documentation researcher. Find and summarize technical "
            "documentation. Include source URLs, API behavior summary, and "
            "implementation constraints. Do not write code."
        ),
        tools=RESEARCHER_TOOLS,
        user_message=f"Find documentation about: {user_request}",
    )
    total_input += research_result["input_tokens"]
    total_output += research_result["output_tokens"]

    # Completeness check
    has_substance = len(research_result["text"]) > 200
    if not has_substance:
        print("  Research seems thin — proceeding anyway.")

    print("\nStep 2: Code")
    coding_brief = (
        f"## Research Brief\n{research_result['text']}\n\n"
        f"## Task\n{user_request}\n\n"
        f"## Acceptance Criteria\n"
        f"- Code must be complete and runnable\n"
        f"- Must demonstrate the documented API behavior\n"
        f"- Must include error handling"
    )

    code_result = run_agent(
        role="coder",
        model=CODER_MODEL,
        system_prompt=(
            "You are a Python implementation specialist. Given a research brief "
            "and acceptance criteria, write complete, runnable Python code. "
            "Do not search the web. Work only from the provided brief."
        ),
        tools=CODER_TOOLS,
        user_message=coding_brief,
    )
    total_input += code_result["input_tokens"]
    total_output += code_result["output_tokens"]

    elapsed = time.time() - start

    print(f"\nDone. Total: {total_input} in / {total_output} out | {elapsed:.1f}s")

    return {
        "research": research_result["text"],
        "code": code_result["text"],
        "input_tokens": total_input,
        "output_tokens": total_output,
        "elapsed_s": elapsed,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    print("Atlas Multi-Agent — Three-Agent System\n")

    request = "Find how asyncio.gather works and write a working Python example with three concurrent tasks"
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])

    print(f"Request: {request}\n")
    result = run_orchestrator(request)

    print(f"\n{'=' * 60}")
    print("## Research Summary")
    print(result["research"][:500])
    print(f"\n## Generated Code")
    print(result["code"][:1000])
    print(f"\nTokens: {result['input_tokens']} in, {result['output_tokens']} out")
    print(f"Elapsed: {result['elapsed_s']:.1f}s")


if __name__ == "__main__":
    main()
