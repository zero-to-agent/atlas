# Atlas — Chapter 7: The Agent Loop

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-6
- Take a goal and work autonomously toward completing it
- Generate a numbered plan before taking action
- Execute multiple tool calls across iterations
- Stop safely on: completion, timeout, budget, max iterations, or approval denial
- Optionally require human approval for write and execute operations

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
python atlas_v6.py "Research the top 3 Python HTTP libraries and write a comparison to comparison.md"
```

## Files

| File | Description |
|------|-------------|
| `atlas_v6.py` | Autonomous agent loop with planning, guardrails, approval gates |
| `atlas_v5.py` | Tool infrastructure from Chapter 6 |
| `atlas_v4.py` | Structured output from Chapter 5 |
| `atlas_v3.py` | Conversation REPL from Chapter 4 |
| `atlas_v2.py` | Persona and templates from Chapter 3 |
| `atlas_v1.py` | CLI script from Chapter 2 |

## Acceptance Test

```bash
python atlas_v6.py "Research the top 3 Python HTTP libraries and write a comparison to comparison.md"
cat workspace/comparison.md
```

Verify:
- Atlas creates a numbered plan before its first tool call
- Performs 2-3 web searches
- Writes `comparison.md`
- Stops with TASK_COMPLETE signal

## Next Chapter

Chapter 8: RAG: Giving Your Agent Knowledge — `git checkout ch08`
