# Atlas — Chapter 11: Evaluation and Testing

> From **Zero to Agent: From First API Call to Production AI Agents**

## What Atlas can do at this point

- All capabilities from Chapters 2-10
- Run a reproducible eval suite of 20 named cases
- Assert on tool selection, forbidden tools, and guardrail compliance
- Gate merges in CI when pass rate drops below 85%
- Export eval results as JSON artifacts for trending

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Add your API keys
pytest tests/eval_suite.py -v --min-pass-rate 0.85
```

## Files

| File | Description |
|------|-------------|
| `tests/conftest.py` | Pytest plugin with eval tracking and pass-rate gating |
| `tests/eval_suite.py` | Parametrized eval runner |
| `tests/eval_cases.json` | 20 eval cases (tool selection, guardrails, regression) |
| `.github/workflows/eval.yml` | CI workflow for eval automation |

## Acceptance Test

```bash
pytest tests/eval_suite.py -v --min-pass-rate 0.85
# Verify pass rate >= 85%
cat eval_results.json
```

## Next Chapter

Chapter 12: Going to Production — `git checkout ch12`
