"""Custom exception classes for the API service."""


class AppError(Exception):
    """Base class for all application-specific exceptions.

    Attributes:
        message: Human-readable error description.
        status_code: Suggested HTTP status code for the error response.
    """

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(AppError):
    """Raised when an API key or credential check fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class TokenExpiredError(AppError):
    """Raised when a session token has exceeded its time-to-live."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, status_code=401)


class DatabaseError(AppError):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)


class ValidationError(AppError):
    """Raised when user input fails validation rules."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class RateLimitError(AppError):
    """Raised when a client exceeds the allowed request rate."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
