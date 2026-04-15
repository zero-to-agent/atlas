"""Application entry point for the REST API service."""

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

from config import settings
from constants import API_VERSION, CONTENT_TYPE_JSON, LOG_FORMAT
from database import init_schema
from middleware import auth_middleware, logging_middleware
from routes import dispatch

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080


class RequestHandler(BaseHTTPRequestHandler):
    """Minimal HTTP request handler that delegates to the route registry."""

    def _read_body(self) -> Dict[str, Any]:
        """Parse the JSON request body, returning an empty dict on failure."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _handle(self, method: str) -> None:
        """Shared handler logic for all HTTP methods."""
        body = self._read_body()
        headers = {k: v for k, v in self.headers.items()}

        def inner(b: Dict[str, Any]):
            return dispatch(method, self.path, b)

        status, response = auth_middleware(inner, method, self.path, body, headers)
        status, response = logging_middleware(lambda b: (status, response), method, self.path, body)

        self.send_response(status)
        self.send_header("Content-Type", CONTENT_TYPE_JSON)
        self.send_header("X-API-Version", API_VERSION)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")


def main() -> None:
    """Start the HTTP server after initializing the database schema."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logger = logging.getLogger(__name__)

    init_schema()

    host = settings.get("HOST", DEFAULT_HOST)
    port = int(settings.get("PORT", DEFAULT_PORT))

    server = HTTPServer((host, port), RequestHandler)
    logger.info("Server started on %s:%d (API %s)", host, port, API_VERSION)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
