"""Configuration loading utilities for the enhanced automation agent."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

try:  # pragma: no cover - allow tests without PyYAML
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    yaml = None


@dataclass(frozen=True)
class BulkConfig:
    max_concurrent: int
    retry_attempts: int
    retry_delay_seconds: int


@dataclass(frozen=True)
class PauseAfterErrorConfig:
    threshold: int
    duration_s: int


@dataclass(frozen=True)
class GovernanceConfig:
    cpu_high_pct: float
    mem_high_pct: float
    window_s: int
    pause_after_error_burst: PauseAfterErrorConfig
    human_review_after_pause_bursts: int


@dataclass(frozen=True)
class TelemetryConfig:
    sample_interval_s: int
    log_interval_s: int


@dataclass(frozen=True)
class PersistenceConfig:
    db_path: Path
    gc_completed_after_days: int


@dataclass(frozen=True)
class EscalationConfig:
    enabled: bool
    webhook_url: Optional[str]
    email_to: Optional[str]


@dataclass(frozen=True)
class AgentConfig:
    bulk: BulkConfig
    governance: GovernanceConfig
    telemetry: TelemetryConfig
    persistence: PersistenceConfig
    escalation: EscalationConfig


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment overrides using SANAAGENT_* variables."""
    mapping = {
        "SANAAGENT_BULK_MAX_CONCURRENT": ("bulk", "max_concurrent"),
        "SANAAGENT_BULK_RETRY_ATTEMPTS": ("bulk", "retry_attempts"),
        "SANAAGENT_BULK_RETRY_DELAY_SECONDS": ("bulk", "retry_delay_seconds"),
        "SANAAGENT_GOV_CPU_HIGH_PCT": ("governance", "cpu_high_pct"),
        "SANAAGENT_GOV_MEM_HIGH_PCT": ("governance", "mem_high_pct"),
        "SANAAGENT_GOV_WINDOW_S": ("governance", "window_s"),
        "SANAAGENT_GOV_PAUSE_THRESHOLD": ("governance", "pause_after_error_burst", "threshold"),
        "SANAAGENT_GOV_PAUSE_DURATION": ("governance", "pause_after_error_burst", "duration_s"),
        "SANAAGENT_GOV_HUMAN_REVIEW_AFTER": ("governance", "human_review_after_pause_bursts"),
        "SANAAGENT_TELEMETRY_SAMPLE_INTERVAL": ("telemetry", "sample_interval_s"),
        "SANAAGENT_TELEMETRY_LOG_INTERVAL": ("telemetry", "log_interval_s"),
        "SANAAGENT_DB_PATH": ("persistence", "db_path"),
        "SANAAGENT_DB_GC_DAYS": ("persistence", "gc_completed_after_days"),
        "SANAAGENT_ESCALATION_ENABLED": ("escalation", "enabled"),
        "SANAAGENT_ESCALATION_WEBHOOK": ("escalation", "webhook_url"),
        "SANAAGENT_ESCALATION_EMAIL": ("escalation", "email_to"),
    }
    for env, keys in mapping.items():
        if env not in os.environ:
            continue
        value: Any = os.environ[env]
        if env.endswith("ENABLED"):
            value = value.lower() in {"1", "true", "yes", "on"}
        elif env.startswith("SANAAGENT_BULK") or env.endswith("PCT") or env.endswith("S") or env.endswith("ATTEMPTS") or env.endswith("DAYS"):
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                raise ValueError(f"Invalid numeric override for {env}: {value}")
        target = config
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
    return config


def load_config(path: Optional[str] = None) -> AgentConfig:
    """Load configuration from YAML file and environment overrides."""
    file_path = Path(path) if path else Path("config.yml")
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as handle:
        contents = handle.read()
        if yaml is not None:
            raw_config = yaml.safe_load(contents) or {}
        else:
            raw_config = json.loads(contents)
    config_dict = _apply_env_overrides(raw_config)

    bulk = BulkConfig(
        max_concurrent=int(config_dict["bulk"]["max_concurrent"]),
        retry_attempts=int(config_dict["bulk"]["retry_attempts"]),
        retry_delay_seconds=int(config_dict["bulk"]["retry_delay_seconds"]),
    )
    pause_conf = PauseAfterErrorConfig(
        threshold=int(config_dict["governance"]["pause_after_error_burst"]["threshold"]),
        duration_s=int(config_dict["governance"]["pause_after_error_burst"]["duration_s"]),
    )
    governance = GovernanceConfig(
        cpu_high_pct=float(config_dict["governance"]["cpu_high_pct"]),
        mem_high_pct=float(config_dict["governance"]["mem_high_pct"]),
        window_s=int(config_dict["governance"]["window_s"]),
        pause_after_error_burst=pause_conf,
        human_review_after_pause_bursts=int(
            config_dict["governance"]["human_review_after_pause_bursts"]
        ),
    )
    telemetry = TelemetryConfig(
        sample_interval_s=int(config_dict["telemetry"]["sample_interval_s"]),
        log_interval_s=int(config_dict["telemetry"]["log_interval_s"]),
    )
    persistence = PersistenceConfig(
        db_path=Path(config_dict["persistence"]["db_path"]),
        gc_completed_after_days=int(config_dict["persistence"]["gc_completed_after_days"]),
    )
    escalation_raw = config_dict.get("escalation", {})
    escalation = EscalationConfig(
        enabled=bool(escalation_raw.get("enabled", False)),
        webhook_url=escalation_raw.get("webhook_url"),
        email_to=escalation_raw.get("email_to"),
    )
    return AgentConfig(
        bulk=bulk,
        governance=governance,
        telemetry=telemetry,
        persistence=persistence,
        escalation=escalation,
    )


__all__ = [
    "AgentConfig",
    "BulkConfig",
    "GovernanceConfig",
    "TelemetryConfig",
    "PersistenceConfig",
    "EscalationConfig",
    "load_config",
]
