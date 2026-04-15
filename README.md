# Atlas — Chapter 3: Prompt Engineering That Actually Works

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- Send prompts to Claude with streaming and error handling (`atlas_v1.py`)
- Maintain a stable persona via a versioned system prompt
- Select task-specific few-shot examples with `build_prompt()`
- Compare three reasoning modes: plain, chain-of-thought, and extended thinking

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your Anthropic API key
python atlas_v2.py
```

## Files

| File | Description |
|------|-------------|
| `atlas_v2.py` | Persona, few-shot templates, reasoning mode comparison |
| `atlas_v1.py` | CLI script from Chapter 2 |

## Acceptance Test

```bash
python atlas_v2.py
```

Verify:
- All 5 persona consistency runs use a concise, code-oriented style
- Code review output uses Bugs/Style/Suggestion headings
- All three reasoning modes produce the correct answer (9)

## Next Chapter

Chapter 4: Conversations and Context — `git checkout ch04`
