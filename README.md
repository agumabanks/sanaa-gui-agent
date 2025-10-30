# Enhanced Automation Agent

The enhanced automation agent executes automation workloads with durable task persistence, governed concurrency, and closed-loop performance management. Tasks are stored in SQLite, retried with exponential backoff, and supervised by a governance controller that reacts to CPU, memory, and error bursts.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run the agent (register handlers in Python first, see below)
python enhanced_automation_agent.py resume
```

### Registering Handlers

```python
from enhanced_automation_agent import EnhancedAutomationAgent

agent = EnhancedAutomationAgent()

def demo_handler(payload: dict[str, int]) -> dict[str, int]:
    return {"result": payload["value"]}

agent.register_handler("demo", demo_handler)
```

Handlers receive the JSON payload persisted with each task and return a JSON-serialisable dictionary that is stored as the task result.

### Enqueuing Work

```bash
python enhanced_automation_agent.py enqueue demo '{"value": 42}'
```

The agent stores the task with an idempotency-safe record. If a task with the same idempotency key has already succeeded, the original result is reused.

## Configuration

Agent behaviour is driven by `config.yml`:

```yaml
bulk:
  max_concurrent: 8
  retry_attempts: 3
  retry_delay_seconds: 15

governance:
  cpu_high_pct: 85
  mem_high_pct: 85
  window_s: 30
  pause_after_error_burst:
    threshold: 10
    duration_s: 60
  human_review_after_pause_bursts: 3

telemetry:
  sample_interval_s: 2
  log_interval_s: 10

persistence:
  db_path: state.db
  gc_completed_after_days: 7

escalation:
  enabled: true
  webhook_url: "http://localhost:8080/hook"
  email_to: "ops@example.local"
```

Set environment overrides using the `SANAAGENT_*` variables. For example, `SANAAGENT_BULK_MAX_CONCURRENT=4` limits concurrency to four workers without editing the file.

## Persistence & Recovery

Tasks are written to SQLite (WAL mode) with the lifecycle `queued → reserved → in_progress → succeeded | failed | retry_scheduled`. On restart the agent requeues stale `reserved` or `in_progress` entries whose heartbeat is older than twice the telemetry interval. Results and error messages are retained, and successful tasks with idempotency keys are never re-executed.

To recover from a crash:

1. Restart the agent (`python enhanced_automation_agent.py resume`).
2. The startup sequence requeues stale in-flight rows and resumes execution without duplicating work.
3. Inspect task status with `python enhanced_automation_agent.py inspect <task_id>`.

## Governance & Telemetry

The governance controller samples CPU, memory, and operation/error counts every `telemetry.sample_interval_s` seconds and stores metrics in both `logs/metrics.jsonl` and the SQLite `metrics` table. Interventions:

- **Throttle**: When CPU or memory exceed thresholds across the window, `max_concurrent` is reduced stepwise.
- **Pause**: Error bursts trigger a temporary pause (queue pulls stop while inflight tasks finish).
- **Escalate**: Repeated pauses within the window send an escalation payload to the configured webhook.
- **Recover**: Healthy windows restore concurrency and lift pauses.

All events are recorded to `logs/agent.jsonl` with JSON-formatted entries for downstream analysis.

## CLI Commands

| Command | Description |
|---------|-------------|
| `enqueue <type> <json>` | Persist a new task. |
| `resume` | Start the agent event loop. Use Ctrl+C to stop. |
| `stats` | Print queue size summary. |
| `inspect <task_id>` | Print the stored record for a task. |

## Tests

Run the automated test suite with:

```bash
pytest -q
```

Tests cover persistence recovery, concurrency throttling and retry semantics, and governance interventions.
