# Atlas — Chapter 5: Structured Output

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- Send prompts with streaming and error handling (`atlas_v1.py`)
- Maintain a stable persona with few-shot templates (`atlas_v2.py`)
- Hold multi-turn conversations with cost tracking (`atlas_v3.py`)
- Classify requests into validated categories with Pydantic models
- Retry with feedback when JSON validation fails
- Route decisions to handlers based on structured output

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your Anthropic API key
python atlas_v4.py "my thing broke and I need help asap"
```

## Files

| File | Description |
|------|-------------|
| `atlas_v4.py` | Pydantic validation, retry-with-feedback, ticket classifier + router |
| `atlas_v3.py` | Multi-turn REPL from Chapter 4 |
| `atlas_v2.py` | Persona and templates from Chapter 3 |
| `atlas_v1.py` | CLI script from Chapter 2 |

## Acceptance Test

```bash
python atlas_v4.py "my thing broke and I need help asap"
# Output should show category=BugReport, priority=High, and a non-empty summary

python atlas_v4.py "Can you add dark mode to the dashboard?"
# Output should show category=FeatureRequest
```

## Next Chapter

Chapter 6: Tool Use — `git checkout ch06`
