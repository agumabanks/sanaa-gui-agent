# Upgrade Notes: Enhanced Automation Agent

## Overview

This upgrade replaces the in-memory queue with a durable SQLite persistence layer and introduces a governed execution engine. Tasks survive restarts, concurrency is dynamically throttled, and metrics drive closed-loop interventions.

## Key Deltas

- **Persistence**: `persistence.TaskStore` manages SQLite tables (`tasks`, `runs`, `metrics`) with WAL mode. Reserved/in-progress tasks older than the heartbeat window are requeued on startup.
- **Concurrency**: `concurrency.TaskExecutor` pulls work respecting `BulkOperationConfig.max_concurrent`, retries via exponential backoff, and integrates CPU-bound handlers via a thread pool.
- **Governance**: `governor.GovernanceController` samples telemetry, logs to JSONL, throttles, pauses, and escalates according to `config.yml` thresholds.
- **Configuration**: `config.load_config` reads YAML with environment overrides to keep operational knobs in a single file.
- **Logging**: Structured JSON logs land in `logs/agent.jsonl`; metrics are mirrored to `logs/metrics.jsonl`.
- **CLI**: `enhanced_automation_agent.py` now exposes `enqueue`, `resume`, `stats`, and `inspect` commands for operators.
- **Tests**: `tests/test_automation_agent.py` verifies persistence recovery, concurrency obedience, retries, and governance triggers.

## Migration Notes

1. Ensure `config.yml` exists (see repo root for defaults). Override `persistence.db_path` for production deployments.
2. Run database migrations implicitly by importing `TaskStore`; the schema is created on first use.
3. Review log rotation strategy for the new `logs/` directory if deploying to long-lived hosts.
4. Update deployment scripts to invoke the CLI or instantiate `EnhancedAutomationAgent` in code, registering handlers before calling `start()`/`run()`.
