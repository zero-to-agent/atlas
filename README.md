# Atlas — Chapter 9: MCP: Connecting to Everything

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-8
- Discover tools dynamically from MCP servers at startup
- Route tool calls to the correct MCP server
- Compose capabilities from multiple servers in one session
- Create custom MCP servers wrapping any REST API

## Prerequisites

- Python 3.11+
- Node.js 18+ (for `npx`-based MCP servers)
- [Anthropic API key](https://console.anthropic.com/)
- [OpenAI API key](https://platform.openai.com/) (for RAG embeddings)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys
python atlas_v8.py "List the Python files in the current directory and summarize the largest one"
```

## Files

| File | Description |
|------|-------------|
| `atlas_v8.py` | MCP client with dynamic tool discovery and multi-server routing |
| `weather_server.py` | Custom MCP server wrapping Open-Meteo weather API |
| `atlas_v7.py` | RAG pipeline from Chapter 8 |
| `atlas_v6.py` | Agent loop from Chapter 7 |
| `atlas_v5.py` | Tool infrastructure from Chapter 6 |

## Acceptance Test

```bash
# Test with filesystem MCP server
python atlas_v8.py "List Python files in the current directory, find the largest, summarize it"

# Test custom weather server
python atlas_v8.py "What is the current weather in Paris?"
```

## Next Chapter

Chapter 10: Multi-Agent Systems — `git checkout ch10`
