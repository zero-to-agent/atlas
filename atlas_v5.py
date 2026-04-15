"""atlas_v5.py — Tool-using assistant with web search, file I/O, and code execution.

Requires: ANTHROPIC_API_KEY environment variable.
Optional: TAVILY_API_KEY for web search.
Usage: python atlas_v5.py "search for Anthropic rate limits and save to rate_limits.txt"
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import anthropic
import requests
from pathlib import Path
from datetime import datetime, timezone

# ============================================================================
# Configuration
# ============================================================================

WORKSPACE_ROOT = Path("./workspace").resolve()
LOG_FILE = Path("./workspace/tool_log.jsonl")
MODEL = "claude-sonnet-4-6"

WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are Atlas, a helpful AI assistant with access to tools. "
    "Use tools when needed to search the web, read files, execute code, or write results. "
    "Always explain your actions to the user."
)

# ============================================================================
# Tool Implementations
# ============================================================================

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily and return formatted results."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set. Set it to use web search."

    response = requests.post(
        "https://api.tavily.com/search",
        json={"query": query, "max_results": max_results, "search_depth": "basic", "api_key": api_key},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for r in data.get("results", []):
        results.append(f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n")
    return "\n---\n".join(results) if results else "No results found."


def read_file(path: str) -> str:
    """Read a file within the workspace directory."""
    requested = (WORKSPACE_ROOT / path).resolve()
    if not requested.is_relative_to(WORKSPACE_ROOT):
        return f"Error: path '{path}' is outside the allowed workspace directory."
    if not requested.is_file():
        return f"Error: file '{path}' does not exist in the workspace."
    return requested.read_text(encoding="utf-8", errors="replace")


def run_python(code: str, timeout: int = 10) -> str:
    """Execute Python code in a subprocess with timeout and output capture."""
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
        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: execution timed out after {timeout} seconds."
    finally:
        Path(script_path).unlink(missing_ok=True)


def write_file(path: str, content: str) -> str:
    """Write content to a file within the workspace directory."""
    requested = (WORKSPACE_ROOT / path).resolve()
    if not requested.is_relative_to(WORKSPACE_ROOT):
        return f"Error: path '{path}' is outside the allowed workspace directory."
    requested.parent.mkdir(parents=True, exist_ok=True)
    requested.write_text(content, encoding="utf-8")
    return f"Successfully wrote {len(content)} characters to {path}."


# ============================================================================
# Tool Registry
# ============================================================================

TOOL_REGISTRY = {
    "web_search": {
        "function": web_search,
        "definition": {
            "name": "web_search",
            "description": "Search the web for current information. Returns titles, URLs, and content snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "max_results": {"type": "integer", "description": "Number of results (1-10).", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    "read_file": {
        "function": read_file,
        "definition": {
            "name": "read_file",
            "description": "Read a file from the workspace directory. Path must be relative to the workspace root.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path, e.g. 'src/main.py'."},
                },
                "required": ["path"],
            },
        },
    },
    "run_python": {
        "function": run_python,
        "definition": {
            "name": "run_python",
            "description": "Execute Python code and return stdout/stderr. Runs in a sandboxed subprocess with timeout.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute."},
                    "timeout": {"type": "integer", "description": "Max seconds to run (default 10).", "default": 10},
                },
                "required": ["code"],
            },
        },
    },
    "write_file": {
        "function": write_file,
        "definition": {
            "name": "write_file",
            "description": "Write text content to a file in the workspace directory. Path must be relative.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path, e.g. 'output/summary.txt'."},
                    "content": {"type": "string", "description": "The text content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
}


def get_tools_payload():
    """Generate the tools list for the API request."""
    return [entry["definition"] for entry in TOOL_REGISTRY.values()]


# ============================================================================
# Validation, Dispatch, and Logging
# ============================================================================

def dispatch_tool(name: str, arguments: dict) -> str:
    """Validate and execute a tool by name."""
    entry = TOOL_REGISTRY.get(name)
    if not entry:
        return f"Error: unknown tool '{name}'."
    return entry["function"](**arguments)


def _redact_sensitive(args: dict) -> dict:
    """Remove API keys or secrets from logged arguments."""
    redacted = {}
    for k, v in args.items():
        if any(secret in k.lower() for secret in ["key", "token", "secret", "password"]):
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = v
    return redacted


def execute_and_log(name: str, arguments: dict) -> str:
    """Execute a tool and log the invocation to disk."""
    start = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    error = None

    try:
        result = dispatch_tool(name, arguments)
        if result.startswith("Error:"):
            error = result
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"
        error = result

    duration_ms = round((time.time() - start) * 1000)
    log_result = result[:500] + "..." if len(result) > 500 else result

    log_entry = {
        "timestamp": timestamp,
        "tool": name,
        "input": _redact_sensitive(arguments),
        "output": log_result,
        "duration_ms": duration_ms,
        "error": error,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result


# ============================================================================
# Tool Call Handling
# ============================================================================

def handle_tool_calls(message):
    """Process all tool_use blocks in a response and return tool results."""
    tool_results = []
    for block in message.content:
        if block.type == "tool_use":
            result = execute_and_log(block.name, block.input)
            is_error = result.startswith("Error:")
            entry = {"type": "tool_result", "tool_use_id": block.id, "content": result}
            if is_error:
                entry["is_error"] = True
            tool_results.append(entry)
    return {"role": "user", "content": tool_results}


# ============================================================================
# Main Conversation
# ============================================================================

def chat(user_message: str) -> str:
    """Run a tool-use exchange: send message, handle tool calls, return final answer."""
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL, max_tokens=4096,
        system=SYSTEM_PROMPT, tools=get_tools_payload(), messages=messages,
    )

    # Loop to handle multiple rounds of tool use
    while response.stop_reason == "tool_use":
        # Print any intermediate text
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"Atlas: {block.text}\n")

        messages.append({"role": "assistant", "content": response.content})
        messages.append(handle_tool_calls(response))

        response = client.messages.create(
            model=MODEL, max_tokens=4096,
            system=SYSTEM_PROMPT, tools=get_tools_payload(), messages=messages,
        )

    # Extract and print final text
    for block in response.content:
        if block.type == "text":
            print(f"Atlas: {block.text}\n")
            return block.text
    return ""


def main():
    print("Atlas v5 — Tool-Using Assistant\n")

    prompt = "Search the web for the current Anthropic API rate limits and save a summary to rate_limits.txt"
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])

    print(f"User: {prompt}\n")
    chat(prompt)

    # Show tool log
    if LOG_FILE.exists():
        print("\n--- Tool Execution Log ---")
        with open(LOG_FILE) as f:
            for line in f:
                entry = json.loads(line)
                print(f"  [{entry['timestamp']}] {entry['tool']} ({entry['duration_ms']}ms)")


if __name__ == "__main__":
    main()
