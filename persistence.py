"""SQLite persistence utilities for the enhanced automation agent."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

UTC = timezone.utc


@dataclass
class TaskRecord:
    """Representation of a persisted task."""

    id: str
    type: str
    payload: Dict[str, Any]
    status: str
    attempts: int
    max_attempts: int
    priority: int
    scheduled_for: datetime
    created_at: datetime
    updated_at: datetime
    idempotency_key: Optional[str]
    last_error: Optional[str]
    result: Optional[Dict[str, Any]]


class TaskStore:
    """Persistence layer wrapping SQLite operations."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    priority INTEGER NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE,
                    last_error TEXT,
                    result TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_scheduled ON tasks(scheduled_for);

                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT NOT NULL,
                    stats TEXT
                );

                CREATE TABLE IF NOT EXISTS metrics (
                    ts TEXT PRIMARY KEY,
                    cpu REAL NOT NULL,
                    mem REAL NOT NULL,
                    errors_count INTEGER NOT NULL,
                    operations_count INTEGER NOT NULL
                );
                """
            )

    @contextmanager
    def _transaction(self) -> Iterable[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def enqueue_task(
        self,
        *,
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: int,
        scheduled_for: datetime,
        max_attempts: int,
        idempotency_key: Optional[str] = None,
    ) -> Optional[TaskRecord]:
        """Insert a new task into the queue, enforcing idempotency."""
        now = datetime.now(tz=UTC)
        with self._transaction() as conn:
            if idempotency_key is not None:
                row = conn.execute(
                    "SELECT * FROM tasks WHERE idempotency_key=? AND status='succeeded'",
                    (idempotency_key,),
                ).fetchone()
                if row:
                    return self._row_to_record(row)
            conn.execute(
                """
                INSERT INTO tasks(id, type, payload, status, attempts, max_attempts, priority,
                                  scheduled_for, created_at, updated_at, idempotency_key)
                VALUES(?, ?, ?, 'queued', 0, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task_type,
                    json.dumps(payload),
                    max_attempts,
                    priority,
                    scheduled_for.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    idempotency_key,
                ),
            )
        return None

    def reserve_batch(self, limit: int) -> List[TaskRecord]:
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as conn:
            rows = conn.execute(
                """
                SELECT id FROM tasks
                WHERE status IN ('queued', 'retry_scheduled') AND scheduled_for <= ?
                ORDER BY priority DESC, scheduled_for ASC
                LIMIT ?
                """,
                (now, limit),
            ).fetchall()
            task_ids = [row[0] for row in rows]
            reserved: List[TaskRecord] = []
            for task_id in task_ids:
                conn.execute(
                    "UPDATE tasks SET status='reserved', updated_at=? WHERE id=?",
                    (now, task_id),
                )
                row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
                if row:
                    reserved.append(self._row_to_record(row))
        return reserved

    def requeue_stale_inflight(self, heartbeat_ttl: timedelta) -> int:
        deadline = datetime.now(tz=UTC) - heartbeat_ttl
        with self._transaction() as conn:
            result = conn.execute(
                """
                UPDATE tasks
                SET status='queued', updated_at=?
                WHERE status IN ('reserved', 'in_progress') AND updated_at < ?
                """,
                (datetime.now(tz=UTC).isoformat(), deadline.isoformat()),
            )
            return result.rowcount

    def mark_in_progress(self, task_id: str) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE tasks SET status='in_progress', attempts=attempts+1, updated_at=? WHERE id=?",
                (datetime.now(tz=UTC).isoformat(), task_id),
            )

    def heartbeat(self, task_id: str) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE tasks SET updated_at=? WHERE id=?",
                (datetime.now(tz=UTC).isoformat(), task_id),
            )

    def complete_task(self, task_id: str, result: Dict[str, Any]) -> None:
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE tasks SET status='succeeded', result=?, updated_at=? WHERE id=?",
                (json.dumps(result), now, task_id),
            )

    def fail_task(self, task_id: str, error: str) -> None:
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE tasks SET status='failed', last_error=?, updated_at=? WHERE id=?",
                (error, now, task_id),
            )

    def schedule_retry(self, task_id: str, scheduled_for: datetime, error: str) -> None:
        with self._transaction() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status='retry_scheduled', scheduled_for=?, last_error=?, updated_at=?
                WHERE id=?
                """,
                (
                    scheduled_for.isoformat(),
                    error,
                    datetime.now(tz=UTC).isoformat(),
                    task_id,
                ),
            )

    def fetch_task(self, task_id: str) -> Optional[TaskRecord]:
        with self._transaction() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row:
                return self._row_to_record(row)
        return None

    def cleanup_completed(self, older_than: timedelta) -> int:
        cutoff = datetime.now(tz=UTC) - older_than
        with self._transaction() as conn:
            result = conn.execute(
                "DELETE FROM tasks WHERE status='succeeded' AND updated_at < ?",
                (cutoff.isoformat(),),
            )
            return result.rowcount

    def insert_metrics(self, ts: datetime, cpu: float, mem: float, errors: int, operations: int) -> None:
        with self._transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO metrics(ts, cpu, mem, errors_count, operations_count) VALUES(?, ?, ?, ?, ?)",
                (ts.isoformat(), cpu, mem, errors, operations),
            )

    def start_run(self, run_id: str) -> None:
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO runs(id, started_at, status) VALUES(?, ?, 'running')",
                (run_id, now),
            )

    def finish_run(self, run_id: str, status: str, stats: Dict[str, Any]) -> None:
        now = datetime.now(tz=UTC).isoformat()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE runs SET ended_at=?, status=?, stats=? WHERE id=?",
                (now, status, json.dumps(stats), run_id),
            )

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> TaskRecord:
        def parse_dt(value: str) -> datetime:
            return datetime.fromisoformat(value)

        result = json.loads(row["result"]) if row["result"] else None
        payload = json.loads(row["payload"]) if row["payload"] else {}
        return TaskRecord(
            id=row["id"],
            type=row["type"],
            payload=payload,
            status=row["status"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            priority=row["priority"],
            scheduled_for=parse_dt(row["scheduled_for"]),
            created_at=parse_dt(row["created_at"]),
            updated_at=parse_dt(row["updated_at"]),
            idempotency_key=row["idempotency_key"],
            last_error=row["last_error"],
            result=result,
        )


__all__ = ["TaskStore", "TaskRecord"]
