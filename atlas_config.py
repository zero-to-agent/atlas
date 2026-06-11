"""atlas_config.py — one source of truth for model IDs (Chapter 2).

Pulled from client.models.list() on 2026-04-15. When these IDs deprecate,
run the command again and update here; importing modules pick up the rename
as a one-line change.
"""

MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-7"

DEFAULT_MODEL = MODEL_SONNET
