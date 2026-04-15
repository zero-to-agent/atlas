# Atlas — Chapter 2: Your First API Call

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- Accept a prompt from the command line and send it to Claude via the Messages API
- Stream the response to the terminal in real time
- Print token usage, stop reason, and per-call cost estimate
- Handle authentication failures, rate limits, and request-size errors gracefully
- Switch between Haiku, Sonnet, and Opus via a `--model` flag
- Enforce a budget guardrail that warns when projected daily cost exceeds a threshold

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your Anthropic API key
python atlas_v1.py "Explain what a token is in one sentence."
```

## Files

| File | Description |
|------|-------------|
| `atlas_v1.py` | CLI script — streaming responses, error handling, cost tracking |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for API keys |

## Acceptance Test

```bash
# Normal run — should stream a response and print usage stats
python atlas_v1.py "Explain what a token is in one sentence."

# Model comparison
python atlas_v1.py "Summarize quantum computing in two sentences." --model claude-haiku-4-5-20251001
python atlas_v1.py "Summarize quantum computing in two sentences." --model claude-opus-4-6

# Error handling — should print a clear error, no traceback
unset ANTHROPIC_API_KEY
python atlas_v1.py "Hello"
```

## Next Chapter

Chapter 3: Prompt Engineering That Actually Works — `git checkout ch03`
