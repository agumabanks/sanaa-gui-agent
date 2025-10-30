"""Concurrency engine for executing persisted automation tasks."""
from __future__ import annotations

import asyncio
import inspect
import logging
import random
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, Optional

from persistence import TaskRecord, TaskStore

UTC = timezone.utc

LOGGER = logging.getLogger("enhanced_agent.concurrency")


@dataclass
class HandlerSpec:
    """Metadata associated with a registered task handler."""

    func: Callable[[Dict[str, object]], Awaitable[dict] | dict]
    cpu_bound: bool = False


class RetryPolicy:
    """Retry helper implementing exponential backoff with jitter."""

    def __init__(self, base_delay: int, max_attempts: int) -> None:
        self.base_delay = base_delay
        self.max_attempts = max_attempts

    def next_delay(self, attempt_number: int) -> float:
        delay = self.base_delay * (2 ** max(0, attempt_number - 1))
        jitter = random.uniform(0, self.base_delay / 3)
        return delay + jitter


class TaskExecutor:
    """Async execution engine with governed concurrency and persistence."""

    def __init__(
        self,
        *,
        store: TaskStore,
        handlers: Dict[str, HandlerSpec],
        max_concurrent: int,
        retry_policy: RetryPolicy,
        operations_counter: "OperationsCounter",
    ) -> None:
        self.store = store
        self.handlers = handlers
        self.retry_policy = retry_policy
        self._max_configured = max_concurrent
        self._effective_max = max_concurrent
        self._operations_counter = operations_counter
        self._shutdown = asyncio.Event()
        self._pause_until: Optional[float] = None
        self._inflight: Dict[str, asyncio.Task[None]] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._loop = asyncio.get_event_loop()

    @property
    def effective_max_concurrent(self) -> int:
        return self._effective_max

    @property
    def configured_max(self) -> int:
        return self._max_configured

    @property
    def inflight_count(self) -> int:
        return len(self._inflight)

    def set_effective_max_concurrent(self, value: int) -> None:
        value = max(1, min(self._max_configured, value))
        if value == self._effective_max:
            return
        LOGGER.info("Adjusting effective concurrency", extra={"value": value})
        self._effective_max = value

    async def pause_for(self, duration: float) -> None:
        LOGGER.warning("Pausing task reservations", extra={"duration": duration})
        self._pause_until = time.time() + duration

    def resume(self) -> None:
        LOGGER.info("Resuming task reservations")
        self._pause_until = None

    def shutdown(self) -> None:
        LOGGER.info("Shutdown requested")
        self._shutdown.set()

    async def _reserve_tasks(self, slots: int) -> list[TaskRecord]:
        if slots <= 0:
            return []
        return await asyncio.to_thread(self.store.reserve_batch, slots)

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self.shutdown)
            except (NotImplementedError, RuntimeError):  # pragma: no cover
                LOGGER.debug("Signal handlers not supported for loop", extra={"signal": sig})
        try:
            while not self._shutdown.is_set():
                if self._pause_until and time.time() < self._pause_until:
                    await asyncio.sleep(0.5)
                    continue
                available = self._effective_max - len(self._inflight)
                if available > 0:
                    tasks = await self._reserve_tasks(available)
                    for task in tasks:
                        await self._start_task(task)
                else:
                    await asyncio.sleep(0.1)
        finally:
            await self._drain()
            self._executor.shutdown(wait=True)

    async def _drain(self) -> None:
        LOGGER.info("Draining in-flight tasks", extra={"count": len(self._inflight)})
        if not self._inflight:
            return
        await asyncio.gather(*self._inflight.values(), return_exceptions=True)

    async def _start_task(self, record: TaskRecord) -> None:
        handler = self.handlers.get(record.type)
        if handler is None:
            LOGGER.error("No handler registered", extra={"task_type": record.type})
            self.store.fail_task(record.id, "handler_not_found")
            self._operations_counter.record_operation(False, record.type)
            return

        async def runner() -> None:
            try:
                await self._execute_with_retry(record, handler)
            finally:
                self._inflight.pop(record.id, None)

        task = asyncio.create_task(runner())
        self._inflight[record.id] = task

    async def _execute_with_retry(self, record: TaskRecord, handler: HandlerSpec) -> None:
        attempts = record.attempts
        max_attempts = min(record.max_attempts, self.retry_policy.max_attempts)
        while attempts < max_attempts:
            self.store.mark_in_progress(record.id)
            attempts += 1
            start_ts = time.time()
            try:
                result = await self._invoke(handler, record.payload)
                self.store.complete_task(record.id, result)
                duration_ms = int((time.time() - start_ts) * 1000)
                LOGGER.info(
                    "task_completed",
                    extra={
                        "task_id": record.id,
                        "status": "succeeded",
                        "attempts": attempts,
                        "duration_ms": duration_ms,
                    },
                )
                self._operations_counter.record_operation(True, record.type)
                return
            except Exception as exc:  # pragma: no cover - defensive log
                duration_ms = int((time.time() - start_ts) * 1000)
                LOGGER.exception(
                    "task_failed",
                    extra={
                        "task_id": record.id,
                        "status": "failed",
                        "attempts": attempts,
                        "duration_ms": duration_ms,
                        "reason": str(exc),
                    },
                )
                self._operations_counter.record_operation(False, record.type)
                if attempts >= max_attempts:
                    self.store.fail_task(record.id, str(exc))
                    return
                delay = self.retry_policy.next_delay(attempts)
                scheduled_for = datetime.now(tz=UTC) + timedelta(seconds=delay)
                self.store.schedule_retry(record.id, scheduled_for, str(exc))
                return
        self.store.fail_task(record.id, "max_attempts_exceeded")

    async def _invoke(self, handler: HandlerSpec, payload: Dict[str, object]) -> dict:
        if inspect.iscoroutinefunction(handler.func):
            return await handler.func(payload)
        if handler.cpu_bound:
            return await self._loop.run_in_executor(self._executor, handler.func, payload)
        return await asyncio.to_thread(handler.func, payload)


class OperationsCounter:
    """Thread-safe structure for tracking operations and error bursts."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._operations: list[tuple[float, bool, str]] = []

    async def snapshot(self, window: float) -> tuple[int, int]:
        async with self._lock:
            now = time.time()
            self._operations = [item for item in self._operations if now - item[0] <= window]
            total = len(self._operations)
            errors = sum(1 for _, success, _ in self._operations if not success)
            return total, errors

    def record_operation(self, success: bool, task_type: str) -> None:
        entry = (time.time(), success, task_type)
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon(self._record, entry)
        except RuntimeError:  # pragma: no cover - fallback for threads
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self._record, entry)
            else:
                self._record(entry)

    def _record(self, entry: tuple[float, bool, str]) -> None:
        self._operations.append(entry)

    async def failing_types(self) -> Dict[str, int]:
        async with self._lock:
            failures: Dict[str, int] = {}
            for _, success, task_type in self._operations:
                if success:
                    continue
                failures[task_type] = failures.get(task_type, 0) + 1
            return failures


__all__ = ["TaskExecutor", "HandlerSpec", "RetryPolicy", "OperationsCounter"]
