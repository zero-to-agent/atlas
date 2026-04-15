"""Input validation functions for request data."""

import re
from typing import Any, Dict, List, Optional

# RFC 5322 simplified email pattern
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Minimum password length enforced at registration
MIN_PASSWORD_LENGTH = 8


def validate_email(email: str) -> bool:
    """Check whether a string looks like a valid email address.

    Uses a simplified pattern that covers the vast majority of real
    addresses without attempting full RFC 5322 compliance.

    Args:
        email: The email string to validate.

    Returns:
        True if the string matches the email pattern.
    """
    return bool(_EMAIL_RE.match(email))


def validate_required_fields(data: Dict[str, Any], fields: List[str]) -> List[str]:
    """Return a list of required fields that are missing or empty.

    Args:
        data: The input dictionary to check.
        fields: Names of required keys.

    Returns:
        A list of field names that are absent or have falsy values.
    """
    return [f for f in fields if not data.get(f)]


def validate_password_strength(password: str) -> Optional[str]:
    """Validate that a password meets minimum complexity rules.

    Rules enforced:
      - At least ``MIN_PASSWORD_LENGTH`` characters
      - Contains at least one digit
      - Contains at least one uppercase letter

    Args:
        password: The candidate password string.

    Returns:
        An error message string if validation fails, or None on success.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit"
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter"
    return None
