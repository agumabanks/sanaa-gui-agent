import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config
from concurrency import HandlerSpec, OperationsCounter, RetryPolicy, TaskExecutor
from governor import GovernanceController, Sample
from persistence import TaskStore
from enhanced_automation_agent import EnhancedAutomationAgent

UTC = timezone.utc


@pytest.fixture(autouse=True)
def _chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(PROJECT_ROOT))
    monkeypatch.chdir(tmp_path)
    config = {
        "bulk": {
            "max_concurrent": 3,
            "retry_attempts": 3,
            "retry_delay_seconds": 1,
        },
        "governance": {
            "cpu_high_pct": 50,
            "mem_high_pct": 50,
            "window_s": 5,
            "pause_after_error_burst": {"threshold": 2, "duration_s": 1},
            "human_review_after_pause_bursts": 1,
        },
        "telemetry": {"sample_interval_s": 1, "log_interval_s": 2},
        "persistence": {"db_path": "state.db", "gc_completed_after_days": 7},
        "escalation": {"enabled": False, "webhook_url": None, "email_to": None},
    }
    Path("config.yml").write_text(json.dumps(config))
    return config


@pytest.mark.asyncio
async def test_task_executor_respects_concurrency_and_retries(tmp_path):
    store = TaskStore(tmp_path / "state.db")
    operations = OperationsCounter()
    policy = RetryPolicy(base_delay=0, max_attempts=3)

    current = 0
    peak = 0
    fail_counts: Dict[str, int] = {}

    async def handler(payload: Dict[str, int]) -> Dict[str, int]:
        nonlocal current, peak
        current += 1
        peak = max(peak, current)
        await asyncio.sleep(0.05)
        current -= 1
        idx = payload["i"]
        if fail_counts.get(idx, 0) < 1:
            fail_counts[idx] = fail_counts.get(idx, 0) + 1
            raise RuntimeError("boom")
        return {"ok": idx}

    handlers = {"demo": HandlerSpec(func=handler, cpu_bound=False)}
    executor = TaskExecutor(
        store=store,
        handlers=handlers,
        max_concurrent=2,
        retry_policy=policy,
        operations_counter=operations,
    )

    now = datetime.now(tz=UTC)
    for i in range(4):
        store.enqueue_task(
            task_id=f"task-{i}",
            task_type="demo",
            payload={"i": i},
            priority=0,
            scheduled_for=now,
            max_attempts=3,
        )

    task = asyncio.create_task(executor.run())
    start = time.time()
    while time.time() - start < 5:
        statuses = [store.fetch_task(f"task-{i}").status for i in range(4)]
        if all(status == "succeeded" for status in statuses):
            break
        await asyncio.sleep(0.1)
    executor.shutdown()
    await task

    assert peak <= 2
    for i in range(4):
        record = store.fetch_task(f"task-{i}")
        assert record is not None
        assert record.status == "succeeded"
        assert record.attempts == 2


@pytest.mark.asyncio
async def test_persistence_recovery(tmp_path):
    config_path = tmp_path / "config.yml"
    config_data = {
        "bulk": {"max_concurrent": 2, "retry_attempts": 3, "retry_delay_seconds": 0},
        "governance": {
            "cpu_high_pct": 90,
            "mem_high_pct": 90,
            "window_s": 5,
            "pause_after_error_burst": {"threshold": 3, "duration_s": 1},
            "human_review_after_pause_bursts": 2,
        },
        "telemetry": {"sample_interval_s": 1, "log_interval_s": 2},
        "persistence": {"db_path": str(tmp_path / "state.db"), "gc_completed_after_days": 7},
        "escalation": {"enabled": False, "webhook_url": None, "email_to": None},
    }
    config_path.write_text(json.dumps(config_data))

    processed: List[int] = []

    async def handler(payload: Dict[str, int]) -> Dict[str, int]:
        processed.append(payload["n"])
        await asyncio.sleep(0.05)
        return {"value": payload["n"]}

    agent = EnhancedAutomationAgent(config_path=str(config_path))
    agent.register_handler("demo", handler)
    task_ids = [agent.enqueue_task("demo", {"n": n}) for n in range(5)]

    run_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.2)
    run_task.cancel()
    agent.shutdown()
    with pytest.raises(asyncio.CancelledError):
        await run_task

    interim_statuses = [agent.store.fetch_task(tid).status for tid in task_ids]
    assert any(status != "succeeded" for status in interim_statuses)

    agent2 = EnhancedAutomationAgent(config_path=str(config_path))
    agent2.register_handler("demo", handler)
    run_task2 = asyncio.create_task(agent2.run())

    start = time.time()
    while time.time() - start < 5:
        succeeded = [agent2.store.fetch_task(tid).status for tid in task_ids]
        if succeeded and all(status == "succeeded" for status in succeeded):
            break
        await asyncio.sleep(0.1)
    agent2.shutdown()
    await run_task2

    assert sorted(processed) == list(range(5))


@pytest.mark.asyncio
async def test_governance_pause_and_escalate(tmp_path, monkeypatch):
    store = TaskStore(tmp_path / "state.db")
    operations = OperationsCounter()

    class FakeExecutor:
        def __init__(self) -> None:
            self._effective = 3
            self._configured = 3
            self.paused = False
            self.pause_duration = None

        @property
        def effective_max_concurrent(self) -> int:
            return self._effective

        @property
        def configured_max(self) -> int:
            return self._configured

        async def pause_for(self, duration: float) -> None:
            self.paused = True
            self.pause_duration = duration

        def set_effective_max_concurrent(self, value: int) -> None:
            self._effective = value

        def resume(self) -> None:
            self.paused = False

    executor = FakeExecutor()
    config = load_config()
    controller = GovernanceController(
        config=config.governance,
        telemetry=config.telemetry,
        escalation=config.escalation,
        store=store,
        executor=executor,  # type: ignore[arg-type]
        operations_counter=operations,
        metrics_log=tmp_path / "metrics.jsonl",
    )

    sample = Sample(ts=time.time(), cpu=10, mem=10, errors=config.governance.pause_after_error_burst.threshold, ops=5)
    controller._samples.append(sample)
    await controller._evaluate(sample)
    assert executor.paused is True
    assert executor.pause_duration == config.governance.pause_after_error_burst.duration_s

    throttle_sample = Sample(ts=time.time(), cpu=90, mem=10, errors=0, ops=5)
    controller._samples.append(throttle_sample)
    await controller._evaluate(throttle_sample)
    assert executor.effective_max_concurrent < executor.configured_max

