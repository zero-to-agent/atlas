# Atlas — Chapter 4: Conversations and Context

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- Send prompts with streaming and error handling (`atlas_v1.py`)
- Maintain a stable persona with few-shot templates (`atlas_v2.py`)
- Hold multi-turn conversations with conversation history management
- Track token usage and cost per turn with prompt caching
- Handle transient API errors with exponential backoff

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your Anthropic API key
python atlas_v3.py
```

## Files

| File | Description |
|------|-------------|
| `atlas_v3.py` | Multi-turn REPL with prompt caching and cost tracking |
| `atlas_v2.py` | Persona and templates from Chapter 3 |
| `atlas_v1.py` | CLI script from Chapter 2 |

## Acceptance Test

```bash
python atlas_v3.py
# Have a 10-turn conversation
# Verify cache_read > 0 after turn 2
# Type :quit to exit
```

## Next Chapter

Chapter 5: Structured Output — `git checkout ch05`
