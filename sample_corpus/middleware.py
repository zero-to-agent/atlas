"""Request middleware for logging and authentication enforcement."""

import logging
import time
from typing import Any, Callable, Dict, Tuple

from auth import authenticate
from exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Paths that do not require an API key
PUBLIC_PATHS = frozenset({"/health", "/login"})


def logging_middleware(
    handler: Callable, method: str, path: str, body: Dict[str, Any]
) -> Tuple[int, Dict[str, Any]]:
    """Wrap a handler to log request timing and status.

    Args:
        handler: The route handler to call.
        method: HTTP method string.
        path: Request path.
        body: Parsed request body.

    Returns:
        The handler's ``(status, response)`` tuple, unchanged.
    """
    start = time.monotonic()
    status, response = handler(body)
    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info("%s %s -> %d (%.1fms)", method, path, status, elapsed_ms)
    return status, response


def auth_middleware(
    handler: Callable, method: str, path: str, body: Dict[str, Any], headers: Dict[str, str]
) -> Tuple[int, Dict[str, Any]]:
    """Enforce API-key authentication on protected routes.

    Reads the ``Authorization`` header, expecting the format
    ``Bearer <api_key>``.  Public paths bypass this check.

    Args:
        handler: The route handler to call after auth succeeds.
        method: HTTP method string.
        path: Request path.
        body: Parsed request body.
        headers: Request headers dict.

    Returns:
        The handler's response on success, or a 401 error response.
    """
    if path in PUBLIC_PATHS:
        return handler(body)

    auth_header = headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return 401, {"error": "Missing or malformed Authorization header"}

    api_key = auth_header[7:]  # strip "Bearer "
    if not authenticate(api_key):
        return 401, {"error": "Invalid API key"}

    return handler(body)
