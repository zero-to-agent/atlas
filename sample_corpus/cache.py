"""Simple in-memory cache with time-to-live (TTL) expiration."""

import time
from typing import Any, Dict, Optional, Tuple

# Internal store: key -> (value, expiry_timestamp)
_store: Dict[str, Tuple[Any, float]] = {}

# Default TTL in seconds
DEFAULT_TTL = 300  # 5 minutes


def get(key: str) -> Optional[Any]:
    """Retrieve a value from the cache if it exists and has not expired.

    Args:
        key: The cache key to look up.

    Returns:
        The cached value, or ``None`` if the key is missing or expired.
    """
    entry = _store.get(key)
    if entry is None:
        return None
    value, expiry = entry
    if time.time() > expiry:
        del _store[key]
        return None
    return value


def set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Store a value in the cache with an optional TTL.

    Args:
        key: The cache key.
        value: The value to store (any picklable object).
        ttl: Time-to-live in seconds.  Uses ``DEFAULT_TTL`` when omitted.
    """
    ttl = ttl if ttl is not None else DEFAULT_TTL
    expiry = time.time() + ttl
    _store[key] = (value, expiry)


def delete(key: str) -> bool:
    """Remove a key from the cache.

    Args:
        key: The cache key to delete.

    Returns:
        True if the key existed and was removed, False otherwise.
    """
    return _store.pop(key, None) is not None


def clear() -> int:
    """Remove all entries from the cache.

    Returns:
        The number of entries that were removed.
    """
    count = len(_store)
    _store.clear()
    return count


def size() -> int:
    """Return the number of entries currently in the cache (including expired)."""
    return len(_store)


def evict_expired() -> int:
    """Remove all expired entries and return the count of evicted items."""
    now = time.time()
    expired_keys = [k for k, (_, exp) in _store.items() if now > exp]
    for k in expired_keys:
        del _store[k]
    return len(expired_keys)
