from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings


class SQLiteStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init(self) -> None:
        with self._lock, self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                  id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  tool_name TEXT NOT NULL,
                  args_json TEXT NOT NULL,
                  args_hash TEXT NOT NULL,
                  risk_level TEXT NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  requested_at TEXT NOT NULL,
                  expires_at TEXT NOT NULL,
                  status TEXT NOT NULL,
                  requested_by_model INTEGER NOT NULL DEFAULT 1,
                  approved_by TEXT,
                  approved_at TEXT,
                  token_hash TEXT,
                  used_at TEXT,
                  schema_version TEXT NOT NULL DEFAULT 'v1',
                  operator_role TEXT,
                  idempotency_key TEXT,
                  command_id TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_approvals_session_status
                  ON approvals(session_id, status, requested_at);

                CREATE TABLE IF NOT EXISTS control_commands (
                  command_id TEXT PRIMARY KEY,
                  idempotency_key TEXT NOT NULL UNIQUE,
                  approval_id TEXT,
                  session_id TEXT NOT NULL,
                  tool_name TEXT NOT NULL,
                  args_hash TEXT NOT NULL,
                  args_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  requested_by TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  bus_ack_id TEXT,
                  result_json TEXT,
                  error TEXT,
                  FOREIGN KEY(approval_id) REFERENCES approvals(id)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  chain_hash TEXT,
                  prev_hash TEXT
                );

                CREATE TABLE IF NOT EXISTS tool_calls (
                  call_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  tool_name TEXT NOT NULL,
                  args_hash TEXT NOT NULL,
                  args_json TEXT NOT NULL,
                  risk_level TEXT NOT NULL,
                  status TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  ended_at TEXT,
                  duration_ms INTEGER,
                  result_json TEXT,
                  error TEXT
                );

                CREATE TABLE IF NOT EXISTS sessions (
                  session_id TEXT PRIMARY KEY,
                  state_json TEXT NOT NULL,
                  version INTEGER NOT NULL DEFAULT 1,
                  updated_at TEXT NOT NULL,
                  expires_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
                  ON sessions(expires_at);

                CREATE TABLE IF NOT EXISTS agent_decisions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT NOT NULL,
                  step_index INTEGER NOT NULL,
                  timestamp TEXT NOT NULL,
                  messages_json TEXT NOT NULL,
                  response_json TEXT NOT NULL,
                  tool_calls_json TEXT NOT NULL,
                  policy_json TEXT NOT NULL,
                  tool_results_json TEXT NOT NULL,
                  latency_ms INTEGER NOT NULL,
                  trace_id TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_agent_decisions_session
                  ON agent_decisions(session_id, step_index, id);
                """
            )
            self._ensure_column(conn, "audit_events", "chain_hash", "TEXT")
            self._ensure_column(conn, "audit_events", "prev_hash", "TEXT")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self._lock, self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(sql, params)
            conn.commit()

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._lock, self.connect() as conn:
            return conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._lock, self.connect() as conn:
            return list(conn.execute(sql, params).fetchall())


store = SQLiteStore(get_settings().waterclaw_sqlite_path)
