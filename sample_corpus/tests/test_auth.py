"""Tests for the auth module."""

import time
import unittest
from unittest.mock import patch

import sys
from pathlib import Path

# Allow imports from the parent package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import authenticate, generate_token, validate_token, TOKEN_TTL_SECONDS
from exceptions import TokenExpiredError


class TestAuthenticate(unittest.TestCase):
    """Tests for the authenticate() function."""

    @patch("auth.settings", {"API_SECRET_KEY": "test-secret-key-123"})
    def test_valid_key_returns_true(self):
        self.assertTrue(authenticate("test-secret-key-123"))

    @patch("auth.settings", {"API_SECRET_KEY": "test-secret-key-123"})
    def test_invalid_key_returns_false(self):
        self.assertFalse(authenticate("wrong-key"))

    @patch("auth.settings", {"API_SECRET_KEY": ""})
    def test_empty_secret_rejects_nonempty_key(self):
        self.assertFalse(authenticate("anything"))

    @patch("auth.settings", {"API_SECRET_KEY": ""})
    def test_empty_key_matches_empty_secret(self):
        self.assertTrue(authenticate(""))


class TestGenerateToken(unittest.TestCase):
    """Tests for token generation."""

    def test_returns_64_char_hex(self):
        token = generate_token("user-1")
        self.assertEqual(len(token), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in token))

    def test_unique_tokens(self):
        tokens = {generate_token("user-1") for _ in range(50)}
        self.assertEqual(len(tokens), 50)


class TestValidateToken(unittest.TestCase):
    """Tests for token validation."""

    def test_valid_token_returns_true(self):
        token = generate_token("user-1")
        self.assertTrue(validate_token(token, time.time()))

    def test_short_token_returns_false(self):
        self.assertFalse(validate_token("tooshort", time.time()))

    def test_expired_token_raises(self):
        token = generate_token("user-1")
        old_time = time.time() - TOKEN_TTL_SECONDS - 100
        with self.assertRaises(TokenExpiredError):
            validate_token(token, old_time)


if __name__ == "__main__":
    unittest.main()
