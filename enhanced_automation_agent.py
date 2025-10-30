"""Enhanced automation agent with durable state, governed concurrency and telemetry."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

try:
    from automation_agent import AutomationAgent, SafetyLevel
except Exception:  # pragma: no cover - fallback for test environments
    from enum import Enum

    class SafetyLevel(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    class AutomationAgent:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.logger = logging.getLogger("enhanced_agent.fallback")

from config import AgentConfig, load_config
from concurrency import HandlerSpec, OperationsCounter, RetryPolicy, TaskExecutor
from governor import GovernanceController
from persistence import TaskStore

UTC = timezone.utc


class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def _setup_logging() -> logging.Logger:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "agent.jsonl"
    logger = logging.getLogger("enhanced_agent")
    logger.setLevel(logging.INFO)
    formatter = JsonFormatter()
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.handlers = [file_handler, stream_handler]
    logger.propagate = False
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.INFO)
    for handler in logger.handlers:
        root.addHandler(handler)
    return logger


class EnhancedAutomationAgent(AutomationAgent):
    """Automation agent backed by durable persistence and governance."""

    def __init__(
        self,
        *,
        config_path: Optional[str] = None,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM,
    ) -> None:
        super().__init__(config_path=None, safety_level=safety_level, log_level=logging.INFO)
        self.logger = _setup_logging()
        self.config: AgentConfig = load_config(config_path)
        self.store = TaskStore(self.config.persistence.db_path)
        self.operations_counter = OperationsCounter()
        self.retry_policy = RetryPolicy(
            base_delay=self.config.bulk.retry_delay_seconds,
            max_attempts=self.config.bulk.retry_attempts,
        )
        self.handlers: Dict[str, HandlerSpec] = {}
        self.executor = TaskExecutor(
            store=self.store,
            handlers=self.handlers,
            max_concurrent=self.config.bulk.max_concurrent,
            retry_policy=self.retry_policy,
            operations_counter=self.operations_counter,
        )
        metrics_log = Path("logs") / "metrics.jsonl"
        self.governor = GovernanceController(
            config=self.config.governance,
            telemetry=self.config.telemetry,
            escalation=self.config.escalation,
            store=self.store,
            executor=self.executor,
            operations_counter=self.operations_counter,
            metrics_log=metrics_log,
        )
        self._heartbeat_ttl = timedelta(seconds=self.config.telemetry.sample_interval_s * 4)
        self._run_task: Optional[asyncio.Task[None]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # Overrides from AutomationAgent disabled
    def start_scheduler(self):  # type: ignore[override]
        raise RuntimeError("Scheduler is managed by the enhanced automation agent")

    def stop_scheduler(self):  # type: ignore[override]
        raise RuntimeError("Scheduler is managed by the enhanced automation agent")

    def register_handler(
        self,
        task_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]] | Dict[str, Any]],
        *,
        cpu_bound: bool = False,
    ) -> None:
        """Register a handler for a given task type."""
        self.handlers[task_type] = HandlerSpec(func=handler, cpu_bound=cpu_bound)
        self.logger.info("handler_registered", extra={"task_type": task_type, "cpu_bound": cpu_bound})

    def enqueue_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        *,
        priority: int = 0,
        scheduled_for: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
        max_attempts: Optional[int] = None,
    ) -> str:
        """Persist a new task, respecting idempotency."""
        task_id = str(uuid.uuid4())
        scheduled = scheduled_for or datetime.now(tz=UTC)
        max_attempts = max_attempts or self.config.bulk.retry_attempts
        previous = self.store.enqueue_task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            scheduled_for=scheduled,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
        )
        if previous is not None:
            self.logger.info(
                "task_deduplicated",
                extra={"task_id": previous.id, "idempotency_key": idempotency_key},
            )
            return previous.id
        self.logger.info(
            "task_enqueued",
            extra={
                "task_id": task_id,
                "task_type": task_type,
                "priority": priority,
                "scheduled_for": scheduled.isoformat(),
                "idempotency_key": idempotency_key,
            },
        )
        return task_id

    async def run(self) -> None:
        """Run the executor and governance loops until shutdown."""
        self._loop = asyncio.get_running_loop()
        await asyncio.to_thread(self.store.requeue_stale_inflight, self._heartbeat_ttl)
        run_id = str(uuid.uuid4())
        self.store.start_run(run_id)
        try:
            await asyncio.gather(self.executor.run(), self.governor.run())
            self.store.finish_run(
                run_id,
                "succeeded",
                {
                    "effective_max": self.executor.effective_max_concurrent,
                },
            )
        except Exception as exc:
            self.store.finish_run(
                run_id,
                "failed",
                {"exception": str(exc)},
            )
            raise

    def start(self) -> None:
        """Start the agent event loop."""
        asyncio.run(self.run())

    def shutdown(self) -> None:
        self.executor.shutdown()
        self.governor.stop()

    async def drain(self, timeout: float = 30.0) -> None:
        """Wait until all tasks are processed or timeout elapses."""
        deadline = datetime.now(tz=UTC) + timedelta(seconds=timeout)
        while datetime.now(tz=UTC) < deadline:
            await asyncio.sleep(0.5)
            if self.executor.inflight_count == 0:
                break

    def cli(self, argv: Optional[list[str]] = None) -> int:
        parser = argparse.ArgumentParser(description="Enhanced automation agent CLI")
        sub = parser.add_subparsers(dest="command")

        enqueue_cmd = sub.add_parser("enqueue", help="Enqueue a task")
        enqueue_cmd.add_argument("task_type")
        enqueue_cmd.add_argument("payload", help="JSON payload for the task")
        enqueue_cmd.add_argument("--priority", type=int, default=0)
        enqueue_cmd.add_argument("--idempotency-key")

        sub.add_parser("resume", help="Resume processing")
        sub.add_parser("stats", help="Show queue statistics")
        inspect_cmd = sub.add_parser("inspect", help="Inspect a task")
        inspect_cmd.add_argument("task_id")

        args = parser.parse_args(argv)
        if args.command == "enqueue":
            payload = json.loads(args.payload)
            task_id = self.enqueue_task(
                args.task_type,
                payload,
                priority=args.priority,
                idempotency_key=args.idempotency_key,
            )
            print(task_id)
            return 0
        if args.command == "resume":
            self.start()
            return 0
        if args.command == "stats":
            self._print_stats()
            return 0
        if args.command == "inspect":
            self._inspect_task(args.task_id)
            return 0
        parser.print_help()
        return 1

    def _print_stats(self) -> None:
        queued = self.store.reserve_batch(0)
        print(json.dumps({"queued": len(queued)}))

    def _inspect_task(self, task_id: str) -> None:
        task = self.store.fetch_task(task_id)
        if not task:
            print(json.dumps({"error": "not_found"}))
            return
        print(
            json.dumps(
                {
                    "task_id": task.id,
                    "status": task.status,
                    "attempts": task.attempts,
                    "last_error": task.last_error,
                    "result": task.result,
                }
            )
        )


def main() -> None:
    agent = EnhancedAutomationAgent()
    raise SystemExit(agent.cli())


if __name__ == "__main__":
    main()
