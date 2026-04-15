"""HTTP route handlers for the REST API.

Uses a simple handler-registry pattern so the application can run without
a heavy framework dependency.  Each handler receives a parsed request dict
and returns a ``(status_code, body)`` tuple.
"""

import json
import uuid
from typing import Any, Callable, Dict, Tuple

from auth import authenticate, generate_token
from database import execute_query
from models import User
from validators import validate_email, validate_required_fields

# Route registry: (method, path) -> handler
_routes: Dict[Tuple[str, str], Callable] = {}


def route(method: str, path: str):
    """Decorator that registers a handler for the given method and path."""

    def decorator(func: Callable) -> Callable:
        _routes[(method.upper(), path)] = func
        return func

    return decorator


def dispatch(method: str, path: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Look up and invoke the handler for a request.

    Returns:
        A tuple of (HTTP status code, response body dict).
    """
    handler = _routes.get((method.upper(), path))
    if handler is None:
        return 404, {"error": "Not found"}
    return handler(body)


@route("POST", "/login")
def login(body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Authenticate a client and return a session token."""
    api_key = body.get("api_key", "")
    if not authenticate(api_key):
        return 401, {"error": "Invalid API key"}
    token = generate_token(user_id=body.get("user_id", "anon"))
    return 200, {"token": token}


@route("POST", "/users")
def create_user(body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Register a new user account."""
    missing = validate_required_fields(body, ["email", "name"])
    if missing:
        return 400, {"error": f"Missing fields: {', '.join(missing)}"}
    if not validate_email(body["email"]):
        return 400, {"error": "Invalid email address"}
    user_id = str(uuid.uuid4())
    execute_query(
        "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
        (user_id, body["email"], body["name"]),
    )
    return 201, {"id": user_id, "email": body["email"], "name": body["name"]}


@route("GET", "/health")
def health_check(body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Return service health status."""
    return 200, {"status": "ok"}
