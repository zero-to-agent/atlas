# Atlas — Chapter 8: RAG: Giving Your Agent Knowledge

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-7
- Index a local corpus of source files into ChromaDB
- Retrieve relevant chunks via embedding similarity search
- Generate answers grounded in retrieved context with source citations
- Avoid hallucinating facts not present in the indexed documents

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)
- [OpenAI API key](https://platform.openai.com/) (for embeddings)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys
python atlas_v7.py
# Then type: what does the authenticate() function do?
```

## Files

| File | Description |
|------|-------------|
| `atlas_v7.py` | RAG pipeline: indexing, retrieval, cited generation |
| `sample_corpus/` | Sample Python project (~15 files) for RAG indexing |
| `atlas_v6.py` | Agent loop from Chapter 7 |
| `atlas_v5.py` | Tool infrastructure from Chapter 6 |
| `atlas_v4.py` | Structured output from Chapter 5 |
| `atlas_v3.py` | Conversation REPL from Chapter 4 |
| `atlas_v2.py` | Persona and templates from Chapter 3 |
| `atlas_v1.py` | CLI script from Chapter 2 |

## Acceptance Test

```bash
python atlas_v7.py
# Ask: what does the authenticate() function do?
# Verify: answer cites auth.py with correct line range
# Verify: answer mentions API key validation and boolean return
```

## Next Chapter

Chapter 9: MCP: Connecting to Everything — `git checkout ch09`
