"""Database connection and query helpers using SQLite."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from config import settings
from exceptions import DatabaseError

DEFAULT_DB_PATH = settings.get("DATABASE_PATH", "app.db")


@contextmanager
def get_connection(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields a SQLite connection and commits on success.

    Args:
        db_path: Path to the SQLite database file.  Uses the configured
                 default when not supplied.

    Yields:
        An open ``sqlite3.Connection`` with row_factory set to ``sqlite3.Row``.
    """
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise DatabaseError(f"Query failed: {exc}") from exc
    finally:
        conn.close()


def execute_query(sql: str, params: tuple = (), db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Run a SQL query and return results as a list of dicts.

    Args:
        sql: The SQL statement to execute.
        params: Bind parameters for the query.
        db_path: Optional database path override.

    Returns:
        List of dictionaries, one per result row.
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def init_schema(db_path: Optional[str] = None) -> None:
    """Create core tables if they do not already exist.

    Args:
        db_path: Optional database path override.
    """
    with get_connection(db_path) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
