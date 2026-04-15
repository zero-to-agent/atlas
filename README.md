# Atlas — Companion Code

> From **Zero to Agent: From First API Call to Production AI Agents**

This repository contains the complete, runnable code for every chapter of the book. Each chapter has its own branch — check out the branch for the chapter you're reading to get a working starting point.

## Chapters

| Branch | Chapter | What You Build |
|--------|---------|---------------|
| `ch01` | What LLMs Actually Are | Conceptual foundation (no code) |
| `ch02` | Your First API Call | `atlas_v1.py` — CLI script with streaming, error handling, cost tracking |
| `ch03` | Prompt Engineering That Actually Works | `atlas_v2.py` — System prompts, few-shot templates, reasoning modes |
| `ch04` | Conversations and Context | `atlas_v3.py` — Multi-turn REPL with prompt caching and session persistence |
| `ch05` | Structured Output | `atlas_v4.py` — Pydantic validation, retry-with-feedback, ticket classifier |
| `ch06` | Tool Use | `atlas_v5.py` — Tool definitions, execution sandbox, audit logging |
| `ch07` | The Agent Loop | `atlas_v6.py` — Autonomous agent with planning, guardrails, approval gates |
| `ch08` | RAG: Giving Your Agent Knowledge | `atlas_v7.py` — Document indexing, ChromaDB, retrieval with citations |
| `ch09` | MCP: Connecting to Everything | `atlas_v8.py` — MCP client, dynamic tool discovery, custom server |
| `ch10` | Multi-Agent Systems | `atlas_multi.py` — Three-agent system with Agent SDK |
| `ch11` | Evaluation and Testing | Eval framework — pytest runner, LLM judge, CI gating |
| `ch12` | Going to Production | `atlas_service.py` — FastAPI app with logging, caching, circuit breaker |
| `ch13` | The AI-Native Developer | Claude Code hooks and slash commands |

## Quick Start

```bash
# Pick a chapter
git checkout ch02

# Set up
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys

# Run
python atlas_v1.py "Explain what a token is in one sentence."
```

## Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) (required for all chapters)
- Additional API keys for specific chapters (noted in each branch's README)

## Branch Navigation

Each branch is cumulative — `ch07` includes all code from chapters 2 through 7. You can start from any chapter:

```bash
git checkout ch07  # Get everything up to and including Chapter 7
```

## License

MIT
