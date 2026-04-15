# Atlas — Chapter 13: The AI-Native Developer

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-12
- Run a `ruff check` hook after every Python file edit in Claude Code
- Generate pytest files from source modules via `/test-gen` command
- Provide a decision framework for classifying tasks as delegate, co-pilot, or human-led

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)
- [Claude Code](https://claude.ai/code) (for hooks and commands)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# The .claude/ directory contains hook configs and slash commands
# that activate automatically when using Claude Code in this project
```

## Files

| File | Description |
|------|-------------|
| `.claude/settings.json` | PostToolUse hook configuration for ruff check |
| `.claude/hooks/lint-check.sh` | Hook script that runs ruff on edited Python files |
| `.claude/commands/test-gen.md` | `/test-gen` slash command for generating pytest files |
| `atlas_service.py` | Production FastAPI service from Chapter 12 |
| `atlas_multi.py` | Multi-agent system from Chapter 10 |
| `atlas_v1.py` - `atlas_v8.py` | Progressive Atlas versions from Chapters 2-9 |

## Acceptance Test

```bash
# Test the lint hook (in Claude Code)
# 1. Open this project in Claude Code
# 2. Ask Claude to edit a Python file
# 3. Verify ruff check runs automatically after the edit

# Test the /test-gen command (in Claude Code)
# /test-gen sample_corpus/auth.py
# Verify: test file is created and passes
```

## The Complete Journey

You've built Atlas from a single API call to a production multi-agent system:

| Chapter | Capability |
|---------|-----------|
| 2 | First API call with streaming |
| 3 | Stable persona with prompt engineering |
| 4 | Multi-turn conversations with caching |
| 5 | Structured output with validation |
| 6 | Tool use with sandbox and logging |
| 7 | Autonomous agent loop with guardrails |
| 8 | RAG for grounded knowledge |
| 9 | MCP for standardized integrations |
| 10 | Multi-agent coordination |
| 11 | Evaluation and testing |
| 12 | Production deployment |
| 13 | AI-native developer workflows |
