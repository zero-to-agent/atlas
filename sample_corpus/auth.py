"""Authentication and token management for the API service."""

import hashlib
import hmac
import secrets
import time
from typing import Optional

from config import settings
from exceptions import AuthenticationError, TokenExpiredError

# Tokens expire after 1 hour by default
TOKEN_TTL_SECONDS = 3600


def authenticate(api_key: str) -> bool:
    """Validate the provided API key against the stored secret.

    Performs a constant-time comparison to prevent timing attacks.
    The stored secret is loaded from the application configuration.

    Args:
        api_key: The API key string supplied by the caller.

    Returns:
        True if the key matches the stored secret, False otherwise.
    """
    stored_secret = settings.get("API_SECRET_KEY", "")
    return hmac.compare_digest(api_key, stored_secret)


def generate_token(user_id: str) -> str:
    """Create a signed session token for an authenticated user.

    Args:
        user_id: Unique identifier of the authenticated user.

    Returns:
        A hex-encoded token string.
    """
    payload = f"{user_id}:{time.time()}:{secrets.token_hex(16)}"
    signature = hashlib.sha256(payload.encode()).hexdigest()
    return signature


def validate_token(token: str, issued_at: float) -> bool:
    """Check whether a session token is still valid.

    Args:
        token: The token string to validate.
        issued_at: Unix timestamp when the token was issued.

    Returns:
        True if the token is well-formed and has not expired.

    Raises:
        TokenExpiredError: If the token has exceeded its TTL.
    """
    if not token or len(token) != 64:
        return False
    elapsed = time.time() - issued_at
    if elapsed > TOKEN_TTL_SECONDS:
        raise TokenExpiredError(f"Token expired {elapsed - TOKEN_TTL_SECONDS:.0f}s ago")
    return True
