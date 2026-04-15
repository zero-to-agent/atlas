# Atlas — Chapter 10: Multi-Agent Systems

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-9
- Coordinate three specialized agents: orchestrator, researcher, coder
- Route tasks to the right specialist with isolated tool access
- Validate research completeness before handing off to coder
- Use cheaper models (Haiku) for coordination, capable models (Sonnet) for specialist work

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)
- [Tavily API key](https://tavily.com/) (for researcher's web search)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys
python atlas_multi.py "Find how asyncio.gather works and write a working Python example"
```

## Files

| File | Description |
|------|-------------|
| `atlas_multi.py` | Three-agent system: orchestrator, researcher, coder |
| `atlas_v8.py` | MCP client from Chapter 9 |
| `atlas_v7.py` | RAG pipeline from Chapter 8 |
| `atlas_v6.py` | Agent loop from Chapter 7 |
| `atlas_v5.py` | Tool infrastructure from Chapter 6 |

## Acceptance Test

```bash
python atlas_multi.py "Find how asyncio.gather works and write a working Python example with three concurrent tasks"
```

Verify:
- Researcher retrieves documentation with source URLs
- Coder generates runnable asyncio example
- Output includes both explanation and working code

## Next Chapter

Chapter 11: Evaluation and Testing — `git checkout ch11`
