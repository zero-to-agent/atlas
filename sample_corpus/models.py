"""Data models for the API service."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Represents a registered user in the system.

    Attributes:
        id: Unique user identifier (UUID string).
        email: User's email address; must be unique.
        name: Display name.
        created_at: Timestamp of account creation.
    """

    id: str
    email: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialize the user to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Session:
    """An active login session tied to a user.

    Attributes:
        id: Unique session identifier.
        user_id: The ``User.id`` this session belongs to.
        token: Opaque bearer token issued at login.
        created_at: When the session was created.
        expires_at: When the session becomes invalid.
    """

    id: str
    user_id: str
    token: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Return True if the session has passed its expiry time."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict:
        """Serialize the session to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
