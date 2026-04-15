"""General-purpose utility helper functions."""

import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def generate_id() -> str:
    """Generate a new UUID4 string suitable for use as a primary key.

    Returns:
        A lowercase hex UUID without hyphens (32 characters).
    """
    return uuid.uuid4().hex


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    """Convert a human-readable string into a URL-safe slug.

    Lowercases the text, replaces non-alphanumeric runs with hyphens,
    and strips leading/trailing hyphens.

    Args:
        text: The input string to slugify.

    Returns:
        A URL-safe slug version of the input.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """Return the hex digest of a string using the specified hash algorithm.

    Args:
        value: The string to hash.
        algorithm: Hash algorithm name (default ``sha256``).

    Returns:
        Hex-encoded hash string.
    """
    h = hashlib.new(algorithm)
    h.update(value.encode("utf-8"))
    return h.hexdigest()


def paginate(items: List[Any], page: int = 1, page_size: int = 25) -> Dict[str, Any]:
    """Slice a list into a single page and return pagination metadata.

    Args:
        items: The full list of items.
        page: 1-based page number.
        page_size: Number of items per page.

    Returns:
        Dict with ``items``, ``page``, ``page_size``, and ``total`` keys.
    """
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(items),
    }
