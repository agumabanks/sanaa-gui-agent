"""Closed-loop governance controller for the enhanced automation agent."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Optional

import psutil
import requests

from config import EscalationConfig, GovernanceConfig, TelemetryConfig
from concurrency import OperationsCounter, TaskExecutor
from persistence import TaskStore

UTC = timezone.utc
LOGGER = logging.getLogger("enhanced_agent.governor")


@dataclass
class Sample:
    ts: float
    cpu: float
    mem: float
    errors: int
    ops: int


class GovernanceController:
    """Continuously samples telemetry and enforces governance policies."""

    def __init__(
        self,
        *,
        config: GovernanceConfig,
        telemetry: TelemetryConfig,
        escalation: EscalationConfig,
        store: TaskStore,
        executor: TaskExecutor,
        operations_counter: OperationsCounter,
        metrics_log: Path,
    ) -> None:
        self.config = config
        self.telemetry = telemetry
        self.escalation = escalation
        self.store = store
        self.executor = executor
        self.operations_counter = operations_counter
        self._samples: Deque[Sample] = deque()
        self._pause_events: Deque[float] = deque()
        self._shutdown = asyncio.Event()
        self._last_summary = 0.0
        self._metrics_log = metrics_log
        self._metrics_log.parent.mkdir(parents=True, exist_ok=True)
        self._cooldown_until: Optional[float] = None
        self._healthy_since: Optional[float] = None
        self._pause_until: Optional[float] = None

    async def run(self) -> None:
        while not self._shutdown.is_set():
            await self._sample_once()
            await asyncio.sleep(self.telemetry.sample_interval_s)

    def stop(self) -> None:
        self._shutdown.set()

    async def _sample_once(self) -> None:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        ops, errors = await self.operations_counter.snapshot(self.config.window_s)
        ts = time.time()
        sample = Sample(ts=ts, cpu=cpu, mem=mem, errors=errors, ops=ops)
        self._samples.append(sample)
        self._trim_samples(ts)
        await asyncio.to_thread(
            self.store.insert_metrics,
            datetime.fromtimestamp(ts, tz=UTC),
            cpu,
            mem,
            errors,
            ops,
        )
        self._write_metrics_log(sample)
        await self._evaluate(sample)
        if ts - self._last_summary >= self.telemetry.log_interval_s:
            self._log_summary()
            self._last_summary = ts

    def _write_metrics_log(self, sample: Sample) -> None:
        record = {
            "ts": datetime.fromtimestamp(sample.ts, tz=UTC).isoformat(),
            "event": "metrics_sample",
            "cpu_pct": sample.cpu,
            "mem_pct": sample.mem,
            "errors": sample.errors,
            "operations": sample.ops,
        }
        with self._metrics_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def _trim_samples(self, now_ts: float) -> None:
        window = self.config.window_s
        while self._samples and now_ts - self._samples[0].ts > window:
            self._samples.popleft()
        while self._pause_events and now_ts - self._pause_events[0] > 1800:
            self._pause_events.popleft()

    async def _evaluate(self, sample: Sample) -> None:
        cpu_avg = sum(s.cpu for s in self._samples) / max(1, len(self._samples))
        mem_avg = sum(s.mem for s in self._samples) / max(1, len(self._samples))
        ops = sample.ops
        errors = sample.errors

        now_ts = sample.ts
        if errors >= self.config.pause_after_error_burst.threshold:
            await self._trigger_pause(now_ts)
        elif (cpu_avg >= self.config.cpu_high_pct or mem_avg >= self.config.mem_high_pct):
            await self._trigger_throttle(now_ts)
        else:
            await self._attempt_recover(now_ts)

        if (
            self.escalation.enabled
            and len(self._pause_events) >= self.config.human_review_after_pause_bursts
        ):
            await self._escalate(now_ts)

    async def _trigger_pause(self, now_ts: float) -> None:
        duration = self.config.pause_after_error_burst.duration_s
        if self._pause_until and now_ts < self._pause_until:
            return
        self._pause_until = now_ts + duration
        self._pause_events.append(now_ts)
        await self.executor.pause_for(duration)
        LOGGER.warning(
            "governance_pause",
            extra={
                "event": "pause",
                "duration_s": duration,
                "reason": "error_burst",
            },
        )

    async def _trigger_throttle(self, now_ts: float) -> None:
        if self._cooldown_until and now_ts < self._cooldown_until:
            return
        new_value = max(1, self.executor.effective_max_concurrent - 1)
        self.executor.set_effective_max_concurrent(new_value)
        self._cooldown_until = now_ts + self.config.window_s
        LOGGER.warning(
            "governance_throttle",
            extra={
                "event": "throttle",
                "reason": "resource_pressure",
                "effective_max": new_value,
            },
        )

    async def _attempt_recover(self, now_ts: float) -> None:
        healthy = True
        if self._samples:
            cpu_avg = sum(s.cpu for s in self._samples) / len(self._samples)
            mem_avg = sum(s.mem for s in self._samples) / len(self._samples)
            if cpu_avg >= self.config.cpu_high_pct or mem_avg >= self.config.mem_high_pct:
                healthy = False
        if self._pause_until and now_ts < self._pause_until:
            healthy = False
        if not healthy:
            self._healthy_since = None
            return
        if self._healthy_since is None:
            self._healthy_since = now_ts
            return
        if now_ts - self._healthy_since >= self.config.window_s:
            if self.executor.effective_max_concurrent < self.executor.configured_max:
                self.executor.set_effective_max_concurrent(
                    self.executor.effective_max_concurrent + 1
                )
                LOGGER.info(
                    "governance_recover",
                    extra={
                        "event": "recover",
                        "effective_max": self.executor.effective_max_concurrent,
                    },
                )
            if self._pause_until and now_ts >= self._pause_until:
                self.executor.resume()
                self._pause_until = None
                LOGGER.info("governance_resume", extra={"event": "resume"})

    def _log_summary(self) -> None:
        if not self._samples:
            return
        cpu_avg = sum(s.cpu for s in self._samples) / len(self._samples)
        mem_avg = sum(s.mem for s in self._samples) / len(self._samples)
        errors = sum(s.errors for s in self._samples)
        record = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "event": "governance_summary",
            "cpu_avg": cpu_avg,
            "mem_avg": mem_avg,
            "active_samples": len(self._samples),
            "effective_max": self.executor.effective_max_concurrent,
            "pause_events": len(self._pause_events),
            "errors_samples": errors,
        }
        with self._metrics_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    async def _escalate(self, now_ts: float) -> None:
        if not self.escalation.enabled:
            return
        self.escalation.enabled = False  # avoid repeated escalations within run
        failures = await self.operations_counter.failing_types()
        payload = {
            "ts": datetime.fromtimestamp(now_ts, tz=UTC).isoformat(),
            "reason": "repeated_pause",
            "current_max_concurrent": self.executor.effective_max_concurrent,
            "window_stats": {
                "cpu_avg": sum(s.cpu for s in self._samples) / max(1, len(self._samples)),
                "mem_avg": sum(s.mem for s in self._samples) / max(1, len(self._samples)),
                "errors": sum(s.errors for s in self._samples),
                "ops": sum(s.ops for s in self._samples),
            },
            "top_error_types": failures,
            "last_50_log_lines": self._tail_logs(50),
        }
        LOGGER.error("governance_escalation", extra={"event": "escalate", "payload": payload})
        if self.escalation.webhook_url:
            await asyncio.to_thread(requests.post, self.escalation.webhook_url, json=payload)

    def _tail_logs(self, n: int) -> list[str]:
        if not self._metrics_log.exists():
            return []
        with self._metrics_log.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
        return [line.strip() for line in lines[-n:]]


__all__ = ["GovernanceController"]
