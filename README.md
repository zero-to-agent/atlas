# Atlas — Chapter 6: Tool Use

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-5
- Call four tools: `web_search`, `read_file`, `write_file`, `run_python`
- Validate tool arguments before execution
- Log every tool call to `workspace/tool_log.jsonl` with timing and redaction
- Handle multiple rounds of tool use in a single conversation
- Sandbox code execution with timeouts and workspace isolation

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)
- [Tavily API key](https://tavily.com/) (optional, for web search)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys
python atlas_v5.py "search for the current Anthropic API rate limits and save a summary to rate_limits.txt"
```

## Files

| File | Description |
|------|-------------|
| `atlas_v5.py` | Tool-using assistant with registry, validation, and logging |
| `atlas_v4.py` | Structured output from Chapter 5 |
| `atlas_v3.py` | Conversation REPL from Chapter 4 |
| `atlas_v2.py` | Persona and templates from Chapter 3 |
| `atlas_v1.py` | CLI script from Chapter 2 |

## Acceptance Test

```bash
python atlas_v5.py "search for the current Anthropic API rate limits and save a summary to rate_limits.txt"
# Atlas should: perform web_search, write_file, log all tool calls
cat workspace/rate_limits.txt
cat workspace/tool_log.jsonl
```

## Next Chapter

Chapter 7: The Agent Loop — `git checkout ch07`
