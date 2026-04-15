# Atlas — Chapter 12: Going to Production

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-11
- Serve as a production HTTP service via FastAPI
- Structured JSON logging for every LLM call
- Cost accounting persisted to SQLite with budget alerts
- Prompt caching, response caching, and model routing
- Rate limiting, circuit breaker, and retry with backoff
- PII redaction and prompt injection defense

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys
uvicorn atlas_service:app --reload
```

## Files

| File | Description |
|------|-------------|
| `atlas_service.py` | FastAPI app with /chat, /health, /cost-today endpoints |
| `tests/` | Eval framework from Chapter 11 |
| `atlas_multi.py` | Multi-agent system from Chapter 10 |

## Acceptance Test

```bash
# Start the server
uvicorn atlas_service:app &

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Python?"}'

# Check health
curl http://localhost:8000/health

# Check cost
curl http://localhost:8000/cost-today
```

## Next Chapter

Chapter 13: The AI-Native Developer — `git checkout ch13`
