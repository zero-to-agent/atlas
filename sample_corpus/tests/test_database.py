"""Tests for the database module."""

import os
import tempfile
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import execute_query, get_connection, init_schema
from exceptions import DatabaseError


class TestDatabase(unittest.TestCase):
    """Integration tests using a temporary SQLite database."""

    def setUp(self):
        """Create a temporary database file for each test."""
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        init_schema(self.db_path)

    def tearDown(self):
        """Remove the temporary database."""
        os.unlink(self.db_path)

    def test_init_schema_creates_users_table(self):
        rows = execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'",
            db_path=self.db_path,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "users")

    def test_insert_and_select_user(self):
        execute_query(
            "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
            ("u1", "alice@example.com", "Alice"),
            db_path=self.db_path,
        )
        rows = execute_query(
            "SELECT * FROM users WHERE id = ?", ("u1",), db_path=self.db_path
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email"], "alice@example.com")

    def test_duplicate_email_raises(self):
        execute_query(
            "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
            ("u1", "bob@example.com", "Bob"),
            db_path=self.db_path,
        )
        with self.assertRaises(DatabaseError):
            execute_query(
                "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
                ("u2", "bob@example.com", "Bob2"),
                db_path=self.db_path,
            )

    def test_get_connection_context_manager(self):
        with get_connection(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 AS val")
            row = cursor.fetchone()
            self.assertEqual(row["val"], 1)


if __name__ == "__main__":
    unittest.main()
