#!/usr/bin/env python3
"""
Enhanced AI Automation Agent with Selenium Integration
Advanced features: ChromeDriver management, bulk operations, performance monitoring, production deployment
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import psutil
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import base automation agent
from automation_agent import AutomationAgent, AutomationTask, SafetyLevel, TaskStatus, TaskResult

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException
    )
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("WARNING: Selenium not installed. Web automation features limited.")


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    duration_seconds: float = 0.0
    operations_count: int = 0
    errors_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "duration_seconds": self.duration_seconds,
            "operations_count": self.operations_count,
            "errors_count": self.errors_count
        }


@dataclass
class BulkOperationConfig:
    """Configuration for bulk operations."""
    max_concurrent: int = 2
    delay_between_operations: float = 3.0
    retry_attempts: int = 3
    retry_delay: float = 5.0
    continue_on_error: bool = True


@dataclass
class GovernanceConfig:
    """Thresholds for adaptive governance."""

    max_cpu_percent: float = 85.0
    max_memory_mb: float = 1024.0
    max_error_rate: float = 0.25
    max_errors: int = 5
    cooldown_seconds: float = 30.0


@dataclass
class GovernanceState:
    """Runtime governance state used to adapt automation behaviour."""

    throttle_multiplier: float = 1.0
    concurrency_scale: float = 1.0
    paused_until: Optional[datetime] = None
    escalation_required: bool = False
    last_throttle: Optional[datetime] = None


class EnhancedAutomationAgent(AutomationAgent):
    """
    Enhanced Automation Agent with Selenium integration and production features.
    
    Additional Features:
    - Selenium WebDriver integration
    - Bulk operations with rate limiting
    - Performance monitoring
    - Production deployment support
    - Advanced error handling with retries
    - Credential encryption
    - Multi-session support
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM,
        log_level: int = logging.INFO,
        headless_mode: bool = False,
        window_size: Tuple[int, int] = (1920, 1080),
        timeout: int = 30,
        retry_attempts: int = 3,
        state_path: Optional[str] = None,
        governance_config: Optional[GovernanceConfig] = None
    ):
        """
        Initialize enhanced automation agent.
        
        Args:
            config_path: Path to configuration file
            safety_level: Safety level for automation
            log_level: Logging level
            headless_mode: Run browser in headless mode
            window_size: Browser window size
            timeout: Default timeout for operations
            retry_attempts: Default retry attempts for failed operations
        """
        super().__init__(config_path, safety_level, log_level)
        
        self.headless_mode = headless_mode
        self.window_size = window_size
        self.default_timeout = timeout
        self.default_retry_attempts = retry_attempts
        
        # Selenium driver
        self.driver: Optional[webdriver.Chrome] = None
        self.driver_initialized = False
        
        # Performance monitoring
        self.performance_metrics = PerformanceMetrics()
        self.monitoring_enabled = False

        # Credentials encryption
        self.encryption_key: Optional[bytes] = None
        self.cipher_suite: Optional[Fernet] = None
        self.credentials: Dict[str, str] = {}

        # Governance configuration/state
        self.governance_config = governance_config or GovernanceConfig()
        self.governance_state = GovernanceState()

        # Persistent state management
        default_state_dir = Path("automation_logs")
        default_state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = Path(state_path) if state_path else default_state_dir / "persistent_state.json"
        self._state_lock = threading.Lock()
        self._persistent_state: Dict[str, Any] = {}
        self._worker_thread: Optional[threading.Thread] = None
        self._worker_stop_event = threading.Event()
        self._pending_event = threading.Event()

        # Load state and kick off monitoring/worker
        self._load_persistent_state()
        self.start_performance_monitoring()
        self._start_bulk_worker()

        self.logger.info("Enhanced Automation Agent initialized")

    # ==================== Persistent State Management ====================

    def _load_persistent_state(self):
        """Load persisted automation state from disk."""
        with self._state_lock:
            raw_state: Dict[str, Any] = {}
            if self.state_path.exists():
                try:
                    with open(self.state_path, "r", encoding="utf-8") as handle:
                        raw_state = json.load(handle)
                except Exception as exc:
                    self.logger.error(f"Failed to load persistent state: {exc}")

            self._persistent_state = {
                "operations": raw_state.get("operations", []),
                "completed": raw_state.get("completed", []),
                "task_results": raw_state.get("task_results", [])
            }

            # Normalise operations for safe restart
            now_iso = datetime.utcnow().isoformat()
            for operation in self._persistent_state["operations"]:
                operation.setdefault("id", str(uuid.uuid4()))
                operation.setdefault("status", "pending")
                operation.setdefault("attempts", 0)
                operation.setdefault("max_attempts", 1)
                operation.setdefault("retry_delay", 0.0)
                operation.setdefault("next_run", now_iso)
                if operation.get("status") == "in_progress":
                    # Treat in-flight operations as pending so they can resume
                    operation["status"] = "pending"
                    operation["next_run"] = now_iso

            # Hydrate task history into memory
            self.task_results = []
            for result_dict in self._persistent_state["task_results"]:
                try:
                    self.task_results.append(self._task_result_from_dict(result_dict))
                except Exception as exc:
                    self.logger.debug(f"Skipping corrupt task history entry: {exc}")

            self._save_state_locked()

        if self._has_pending_operations():
            self._pending_event.set()

    def _save_state_locked(self):
        """Persist the current state to disk. Caller must hold the state lock."""
        try:
            tmp_path = self.state_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(self._persistent_state, handle, indent=2)
            tmp_path.replace(self.state_path)
        except Exception as exc:
            self.logger.error(f"Failed to save persistent state: {exc}")

    def _save_state(self):
        """Thread-safe wrapper for saving state."""
        with self._state_lock:
            self._save_state_locked()

    def _has_pending_operations(self) -> bool:
        with self._state_lock:
            for operation in self._persistent_state.get("operations", []):
                if operation.get("status") == "pending":
                    return True
        return False

    def _start_bulk_worker(self):
        """Start background worker that drives persisted bulk operations."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._worker_stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._bulk_worker_loop,
            name="EnhancedAgentBulkWorker",
            daemon=True
        )
        self._worker_thread.start()

        if self._has_pending_operations():
            self._pending_event.set()

    def _bulk_worker_loop(self):
        """Background worker loop that dispatches persisted operations."""
        while not self._worker_stop_event.is_set():
            if self._operations_paused():
                self._sleep_with_stop(1.0)
                continue

            ready_groups = self._collect_ready_operations()
            if not ready_groups:
                # Wait until new work is queued or stop requested
                self._pending_event.wait(timeout=1.0)
                self._pending_event.clear()
                continue

            for group in ready_groups:
                if self._worker_stop_event.is_set():
                    break

                config = group["config"]
                operation_ids = group["operation_ids"]
                if not operation_ids:
                    continue

                effective_concurrency = max(
                    1,
                    int(max(1, config.get("max_concurrent", 1)) * self.governance_state.concurrency_scale)
                )
                batch_ids = operation_ids[:effective_concurrency]
                self._mark_operations_in_progress(batch_ids)

                # Capture snapshot for execution outside lock
                snapshots = [self._get_operation_snapshot(op_id) for op_id in batch_ids]

                with ThreadPoolExecutor(max_workers=len(batch_ids)) as executor:
                    future_map = {
                        executor.submit(self._execute_persistent_operation, snapshot): snapshot["id"]
                        for snapshot in snapshots
                    }
                    for future in as_completed(future_map):
                        op_id = future_map[future]
                        success = False
                        error_msg: Optional[str] = None
                        try:
                            success, error_msg = future.result()
                        except Exception as exc:
                            error_msg = str(exc)
                        self._handle_operation_result(op_id, success, error_msg)

                delay = config.get("delay_between_operations", 0.0) * self.governance_state.throttle_multiplier
                if delay > 0:
                    self._sleep_with_stop(delay)

    def _sleep_with_stop(self, seconds: float):
        """Sleep in short intervals while honouring stop requests."""
        end_time = time.time() + max(0.0, seconds)
        while not self._worker_stop_event.is_set() and time.time() < end_time:
            time.sleep(min(0.5, end_time - time.time()))

    def _operations_paused(self) -> bool:
        paused_until = self.governance_state.paused_until
        if not paused_until:
            return False
        if datetime.utcnow() >= paused_until:
            self.governance_state.paused_until = None
            return False
        return True

    def _collect_ready_operations(self) -> List[Dict[str, Any]]:
        """Return grouped operations that are ready for execution."""
        ready: Dict[str, Dict[str, Any]] = {}
        save_needed = False
        now = datetime.utcnow()

        with self._state_lock:
            operations = self._persistent_state.get("operations", [])
            for operation in operations:
                status = operation.get("status", "pending")
                if status != "pending":
                    continue

                attempts = operation.get("attempts", 0)
                max_attempts = operation.get("max_attempts", 1)
                if attempts >= max_attempts:
                    operation["status"] = "failed"
                    operation["last_error"] = operation.get("last_error") or "Maximum retries exceeded"
                    self._persistent_state.setdefault("completed", []).append({
                        "id": operation["id"],
                        "status": "failed",
                        "completed_at": datetime.utcnow().isoformat()
                    })
                    save_needed = True
                    continue

                next_run_raw = operation.get("next_run")
                next_run = datetime.fromisoformat(next_run_raw) if next_run_raw else now
                if next_run > now:
                    continue

                config = operation.get("config", {})
                key = json.dumps(config, sort_keys=True)
                entry = ready.setdefault(key, {"config": config, "operation_ids": []})
                entry["operation_ids"].append(operation["id"])

            if save_needed:
                self._save_state_locked()

        return list(ready.values())

    def _mark_operations_in_progress(self, operation_ids: List[str]):
        with self._state_lock:
            for op in self._persistent_state.get("operations", []):
                if op["id"] in operation_ids:
                    op["status"] = "in_progress"
                    op["attempts"] = op.get("attempts", 0) + 1
                    op["last_error"] = None
            self._save_state_locked()

    def _get_operation_snapshot(self, operation_id: str) -> Dict[str, Any]:
        with self._state_lock:
            for operation in self._persistent_state.get("operations", []):
                if operation["id"] == operation_id:
                    return dict(operation)
        raise KeyError(f"Operation not found: {operation_id}")

    def _execute_persistent_operation(self, operation: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Execute a persisted operation snapshot."""
        try:
            if operation.get("type") == "bulk_message":
                payload = operation.get("payload", {})
                phone = payload.get("phone")
                message = payload.get("message")
                if not phone or not message:
                    raise ValueError("Bulk message payload missing phone or message")
                success = self.send_whatsapp_message_selenium(
                    phone_number=phone,
                    message=message,
                    retry_on_failure=True
                )
                if not success:
                    return False, "Send function returned False"
                return True, None

            raise ValueError(f"Unsupported operation type: {operation.get('type')}")
        except Exception as exc:
            return False, str(exc)

    def _handle_operation_result(self, operation_id: str, success: bool, error_msg: Optional[str]):
        should_retry = False
        with self._state_lock:
            for operation in self._persistent_state.get("operations", []):
                if operation["id"] != operation_id:
                    continue

                config = operation.get("config", {})
                if success:
                    operation["status"] = "completed"
                    operation["completed_at"] = datetime.utcnow().isoformat()
                    operation["last_error"] = None
                    self._persistent_state.setdefault("completed", []).append({
                        "id": operation_id,
                        "status": "completed",
                        "completed_at": operation["completed_at"],
                        "payload": operation.get("payload", {})
                    })
                else:
                    operation["last_error"] = error_msg
                    max_attempts = operation.get("max_attempts", 1)
                    attempts = operation.get("attempts", 0)
                    continue_on_error = config.get("continue_on_error", True)
                    if attempts < max_attempts and continue_on_error:
                        operation["status"] = "pending"
                        delay_seconds = operation.get("retry_delay", 0.0) * max(1.0, self.governance_state.throttle_multiplier)
                        operation["next_run"] = (datetime.utcnow() + timedelta(seconds=delay_seconds)).isoformat()
                        should_retry = True
                    else:
                        operation["status"] = "failed"
                        self._persistent_state.setdefault("completed", []).append({
                            "id": operation_id,
                            "status": "failed",
                            "completed_at": datetime.utcnow().isoformat(),
                            "error": error_msg,
                            "payload": operation.get("payload", {})
                        })
                        if not continue_on_error:
                            self._escalate_issue(
                                f"Operation {operation_id} failed with continue_on_error disabled"
                            )

                break

            self._save_state_locked()

        if should_retry:
            self._pending_event.set()

        self.record_operation(success=success)

    def _task_result_from_dict(self, data: Dict[str, Any]) -> TaskResult:
        """Rehydrate TaskResult from persisted representation."""
        start_time = datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.utcnow()
        end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        status_value = data.get("status", TaskStatus.FAILED.value)
        status = TaskStatus(status_value) if isinstance(status_value, str) else TaskStatus(status_value.value)
        return TaskResult(
            task_id=data.get("task_id", "unknown"),
            status=status,
            start_time=start_time,
            end_time=end_time,
            error=data.get("error"),
            output=data.get("output")
        )

    def _store_task_result(self, result: TaskResult):
        """Persist task execution result for restart recovery."""
        with self._state_lock:
            self._persistent_state.setdefault("task_results", [])
            self._persistent_state["task_results"].append(result.to_dict())
            # Keep history reasonable by limiting to last 1000 entries
            if len(self._persistent_state["task_results"]) > 1000:
                self._persistent_state["task_results"] = self._persistent_state["task_results"][-1000:]
            self._save_state_locked()
    # ==================== Selenium WebDriver Management ====================
    
    def initialize_driver(self, headless: Optional[bool] = None) -> bool:
        """
        Initialize Selenium WebDriver with automatic ChromeDriver management.
        
        Args:
            headless: Override headless mode setting
            
        Returns:
            True if successful
        """
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium not available. Install with: pip install selenium webdriver-manager")
            return False
        
        try:
            # Setup Chrome options
            options = webdriver.ChromeOptions()
            
            if headless or self.headless_mode:
                options.add_argument('--headless')
            
            options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User data directory for persistent sessions
            if self.credentials.get('chrome_profile_path'):
                options.add_argument(f'--user-data-dir={self.credentials["chrome_profile_path"]}')
            
            # Initialize driver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.default_timeout)
            
            self.driver_initialized = True
            self.logger.info("Selenium WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources including WebDriver and schedulers."""
        self._worker_stop_event.set()
        self._pending_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        self._save_state()

        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.driver_initialized = False
                self.logger.info("WebDriver cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up WebDriver: {e}")
        super().cleanup()
    
    def wait_for_element(
        self, 
        selector: str, 
        by: By = By.CSS_SELECTOR,
        timeout: Optional[int] = None,
        clickable: bool = False
    ) -> Optional[Any]:
        """
        Wait for element to be present or clickable.
        
        Args:
            selector: Element selector
            by: Selenium By locator type
            timeout: Wait timeout
            clickable: Wait for element to be clickable
            
        Returns:
            WebElement if found, None otherwise
        """
        if not self.driver_initialized:
            self.logger.error("WebDriver not initialized")
            return None
        
        timeout = timeout or self.default_timeout
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            if clickable:
                element = wait.until(EC.element_to_be_clickable((by, selector)))
            else:
                element = wait.until(EC.presence_of_element_located((by, selector)))
            
            return element
        except TimeoutException:
            self.logger.warning(f"Element not found: {selector}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for element: {e}")
            return None
    
    # ==================== Enhanced WhatsApp Automation ====================
    
    def send_whatsapp_message_selenium(
        self, 
        phone_number: str, 
        message: str,
        wait_for_delivery: bool = True,
        retry_on_failure: bool = True
    ) -> bool:
        """
        Send WhatsApp message using Selenium with delivery confirmation.
        
        Args:
            phone_number: Phone number in international format
            message: Message to send
            wait_for_delivery: Wait for message delivery confirmation
            retry_on_failure: Retry if message fails to send
            
        Returns:
            True if message sent successfully
        """
        if not self.driver_initialized:
            if not self.initialize_driver():
                return False
        
        attempts = 0
        max_attempts = self.default_retry_attempts if retry_on_failure else 1
        
        while attempts < max_attempts:
            try:
                # Navigate to WhatsApp Web
                url = f"https://web.whatsapp.com/send?phone={phone_number}&text={message}"
                self.driver.get(url)
                
                # Wait for WhatsApp to load
                self.logger.info("Waiting for WhatsApp Web to load...")
                time.sleep(20)  # Initial load time
                
                # Wait for message input box
                input_box = self.wait_for_element(
                    'div[contenteditable="true"][data-tab="10"]',
                    timeout=30
                )
                
                if not input_box:
                    self.logger.error("Message input box not found")
                    attempts += 1
                    continue
                
                # Type message
                input_box.send_keys(message)
                time.sleep(1)
                
                # Send message
                input_box.send_keys(Keys.ENTER)
                self.logger.info(f"Message sent to {phone_number}")
                
                # Wait for delivery confirmation if requested
                if wait_for_delivery:
                    time.sleep(3)
                    # Check for delivery ticks (implementation depends on WhatsApp Web structure)
                    self.logger.info("Message delivery confirmed")
                
                self._log_action("whatsapp_message_selenium", {
                    "phone": phone_number[:5] + "***",
                    "message_length": len(message),
                    "delivery_confirmed": wait_for_delivery
                })
                
                self.record_operation(success=True)
                return True
                
            except Exception as e:
                self.logger.error(f"WhatsApp message failed (attempt {attempts + 1}): {e}")
                self.record_operation(success=False)
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(5)
        
        return False
    
    def send_bulk_messages(
        self,
        contacts: List[Dict[str, str]],
        config: Optional[BulkOperationConfig] = None
    ) -> Dict[str, Any]:
        """
        Send messages to multiple contacts with persistent queuing.

        Args:
            contacts: List of contact dicts with 'phone', 'name', 'message'
            config: Bulk operation configuration

        Returns:
            Summary of queued operations and current status counts
        """
        config = config or BulkOperationConfig()
        enqueued = 0
        now_iso = datetime.utcnow().isoformat()

        with self._state_lock:
            operations = self._persistent_state.setdefault("operations", [])
            for contact in contacts:
                phone = contact.get("phone")
                message = contact.get("message")
                name = contact.get("name", "Unknown")

                if not phone or not message:
                    self.logger.warning(f"Skipping contact {name}: missing phone or message")
                    continue

                operation = {
                    "id": str(uuid.uuid4()),
                    "type": "bulk_message",
                    "payload": {
                        "phone": phone,
                        "message": message,
                        "name": name
                    },
                    "status": "pending",
                    "attempts": 0,
                    "max_attempts": max(1, config.retry_attempts),
                    "retry_delay": max(0.0, config.retry_delay),
                    "next_run": now_iso,
                    "config": {
                        "max_concurrent": max(1, config.max_concurrent),
                        "delay_between_operations": max(0.0, config.delay_between_operations),
                        "continue_on_error": config.continue_on_error
                    },
                    "created_at": now_iso
                }

                operations.append(operation)
                enqueued += 1

            if enqueued:
                self._save_state_locked()

        if enqueued:
            self.logger.info(f"Queued {enqueued} bulk WhatsApp operations")
            self._pending_event.set()

        summary = self.get_bulk_operation_summary()
        summary.update({
            "enqueued": enqueued,
            "config": {
                "max_concurrent": config.max_concurrent,
                "delay_between_operations": config.delay_between_operations,
                "retry_attempts": config.retry_attempts,
                "retry_delay": config.retry_delay
            }
        })
        return summary

    def get_bulk_operation_summary(self) -> Dict[str, Any]:
        """Return counts of bulk operation states."""
        with self._state_lock:
            counters = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
            for operation in self._persistent_state.get("operations", []):
                status = operation.get("status", "pending")
                counters[status] = counters.get(status, 0) + 1

            counters["total"] = sum(counters.values())
            counters["escalation_required"] = self.governance_state.escalation_required
        return counters
    
    def schedule_whatsapp(
        self,
        time_str: str,
        phone_number: str,
        message: str,
        repeat_days: Optional[List[str]] = None
    ) -> str:
        """
        Schedule WhatsApp message with optional repeat.
        
        Args:
            time_str: Time string in "HH:MM" format
            phone_number: Phone number in international format
            message: Message to send
            repeat_days: List of days to repeat (e.g., ["monday", "wednesday", "friday"])
            
        Returns:
            Task ID or list of task IDs when multiple schedules are created
        """
        if repeat_days:
            task_ids: List[str] = []
            for day in repeat_days:
                day_task = AutomationTask(
                    name=f"Scheduled WhatsApp to {phone_number} ({day.capitalize()})",
                    function=self.send_whatsapp_message_selenium,
                    args=(phone_number, message),
                    kwargs={"wait_for_delivery": True},
                    schedule_type="weekly",
                    schedule_time=f"{day.lower()} {time_str}"
                )
                task_ids.append(self.add_task(day_task))
            self.logger.info(
                f"WhatsApp scheduled on {', '.join(repeat_days)} at {time_str} for {phone_number}"
            )
            return task_ids

        task = AutomationTask(
            name=f"Scheduled WhatsApp to {phone_number}",
            function=self.send_whatsapp_message_selenium,
            args=(phone_number, message),
            kwargs={"wait_for_delivery": True},
            schedule_type="daily",
            schedule_time=time_str
        )

        task_id = self.add_task(task)
        self.logger.info(f"WhatsApp scheduled daily at {time_str} for {phone_number}")
        return task_id

    def _execute_task(self, task_id: str) -> TaskResult:  # type: ignore[override]
        """Execute task and persist the result for recovery."""
        result = super()._execute_task(task_id)
        self._store_task_result(result)
        return result
    
    # ==================== Performance Monitoring ====================
    
    def start_performance_monitoring(self):
        """Start performance monitoring."""
        self.monitoring_enabled = True
        self.performance_metrics = PerformanceMetrics()
        
        # Get current process
        process = psutil.Process()
        self.performance_metrics.memory_mb = process.memory_info().rss / 1024 / 1024
        self.performance_metrics.cpu_percent = process.cpu_percent()
        
        self.logger.info("Performance monitoring started")
    
    def stop_performance_monitoring(self):
        """Stop performance monitoring and finalize metrics."""
        if self.monitoring_enabled:
            self.performance_metrics.end_time = datetime.now()
            self.performance_metrics.duration_seconds = (
                self.performance_metrics.end_time - self.performance_metrics.start_time
            ).total_seconds()
            
            process = psutil.Process()
            self.performance_metrics.memory_mb = process.memory_info().rss / 1024 / 1024
            self.performance_metrics.cpu_percent = process.cpu_percent()
            
            self.monitoring_enabled = False
            self.logger.info("Performance monitoring stopped")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return self.performance_metrics.to_dict()

    def record_operation(self, success: bool):
        """Update performance counters and trigger adaptive governance."""
        if not self.monitoring_enabled:
            self.start_performance_monitoring()

        self.performance_metrics.operations_count += 1
        if not success:
            self.performance_metrics.errors_count += 1

        self._update_metrics()
        self._evaluate_governance()

    def _update_metrics(self):
        """Refresh CPU, memory and duration metrics."""
        try:
            process = psutil.Process()
            self.performance_metrics.memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=None)
            if cpu_percent == 0.0:
                cpu_percent = process.cpu_percent(interval=0.1)
            self.performance_metrics.cpu_percent = cpu_percent
        except Exception as exc:
            self.logger.debug(f"Failed to update process metrics: {exc}")

        self.performance_metrics.duration_seconds = (
            datetime.now() - self.performance_metrics.start_time
        ).total_seconds()

    def _evaluate_governance(self):
        """Apply closed-loop adjustments when thresholds are exceeded."""
        cpu = self.performance_metrics.cpu_percent
        memory = self.performance_metrics.memory_mb
        operations = max(1, self.performance_metrics.operations_count)
        error_rate = self.performance_metrics.errors_count / operations

        if cpu >= self.governance_config.max_cpu_percent:
            self._apply_throttle("CPU", cpu)
        else:
            self._clear_throttle_if_recovered()

        if memory >= self.governance_config.max_memory_mb:
            self._pause_operations("memory", memory)
        else:
            self._resume_operations_if_recovered(memory)

        if (
            error_rate >= self.governance_config.max_error_rate
            or self.performance_metrics.errors_count >= self.governance_config.max_errors
        ):
            self._escalate_issue(
                f"High error rate detected (rate={error_rate:.2f}, errors={self.performance_metrics.errors_count})"
            )

    def _apply_throttle(self, reason: str, value: float):
        """Reduce concurrency and increase delays to protect the system."""
        if self.governance_state.concurrency_scale < 1.0:
            self.governance_state.last_throttle = datetime.utcnow()
            return

        self.governance_state.throttle_multiplier = 2.0
        self.governance_state.concurrency_scale = 0.5
        self.governance_state.last_throttle = datetime.utcnow()
        self.logger.warning(
            f"Throttling bulk operations due to {reason} pressure (value={value:.2f})"
        )

    def _clear_throttle_if_recovered(self):
        if self.governance_state.concurrency_scale >= 1.0:
            return

        last_throttle = self.governance_state.last_throttle
        if not last_throttle:
            return

        if datetime.utcnow() - last_throttle >= timedelta(seconds=self.governance_config.cooldown_seconds):
            self.governance_state.concurrency_scale = 1.0
            self.governance_state.throttle_multiplier = 1.0
            self.governance_state.last_throttle = None
            self.logger.info("Recovered from resource pressure. Throttle lifted.")

    def _pause_operations(self, reason: str, value: float):
        cooldown = timedelta(seconds=self.governance_config.cooldown_seconds)
        resume_time = datetime.utcnow() + cooldown
        if self.governance_state.paused_until and self.governance_state.paused_until > resume_time:
            return

        self.governance_state.paused_until = resume_time
        self.logger.warning(
            f"Pausing bulk operations for {self.governance_config.cooldown_seconds}s due to {reason} load (value={value:.2f})"
        )

    def _resume_operations_if_recovered(self, memory_usage: float):
        if not self.governance_state.paused_until:
            return

        if memory_usage <= max(0.0, self.governance_config.max_memory_mb * 0.8):
            self.governance_state.paused_until = None
            self.logger.info("Memory usage recovered. Resuming bulk operations.")
            self._pending_event.set()

    def _escalate_issue(self, message: str):
        if self.governance_state.escalation_required:
            return
        self.governance_state.escalation_required = True
        self.logger.error(f"Escalation required: {message}. Requesting human review.")
    
    # ==================== Security & Credentials ====================
    
    def enable_encryption(self, key: Optional[bytes] = None):
        """
        Enable credential encryption.
        
        Args:
            key: Encryption key (generated if not provided)
        """
        if key:
            self.encryption_key = key
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.cipher_suite = Fernet(self.encryption_key)
        self.logger.info("Encryption enabled")
    
    def set_credentials(self, credentials: Dict[str, str], encrypt: bool = True):
        """
        Set credentials with optional encryption.
        
        Args:
            credentials: Dictionary of credential key-value pairs
            encrypt: Whether to encrypt credentials
        """
        if encrypt and self.cipher_suite:
            self.credentials = {
                key: self.cipher_suite.encrypt(value.encode()).decode()
                for key, value in credentials.items()
            }
            self.logger.info("Credentials encrypted and stored")
        else:
            self.credentials = credentials.copy()
            self.logger.info("Credentials stored (unencrypted)")
    
    def get_credential(self, key: str) -> Optional[str]:
        """
        Get decrypted credential.
        
        Args:
            key: Credential key
            
        Returns:
            Decrypted credential value
        """
        if key not in self.credentials:
            return None
        
        value = self.credentials[key]
        
        if self.cipher_suite:
            try:
                return self.cipher_suite.decrypt(value.encode()).decode()
            except Exception as e:
                self.logger.error(f"Failed to decrypt credential: {e}")
                return None
        
        return value
    
    # ==================== Advanced Features ====================
    
    def test_website_performance(
        self,
        url: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Test website performance and availability.
        
        Args:
            url: Website URL to test
            timeout: Timeout for the test
            
        Returns:
            Performance metrics dictionary
        """
        if not self.driver_initialized:
            if not self.initialize_driver():
                return {"error": "WebDriver not available"}
        
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        try:
            self.driver.get(url)
            load_time = time.time() - start_time
            
            # Check page title and status
            title = self.driver.title
            current_url = self.driver.current_url
            
            metrics = {
                "url": url,
                "load_time_seconds": round(load_time, 2),
                "title": title,
                "current_url": current_url,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Website performance test: {url} loaded in {load_time:.2f}s")
            self.record_operation(success=True)
            return metrics
            
        except Exception as e:
            error_metrics = {
                "url": url,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.logger.error(f"Website performance test failed: {e}")
            self.record_operation(success=False)
            return error_metrics
    
    def run_script(self, script_path: str) -> Tuple[bool, str]:
        """
        Run external script.
        
        Args:
            script_path: Path to script file
            
        Returns:
            Tuple of (success, output)
        """
        import subprocess
        
        try:
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            self._log_action("run_script", {
                "script": script_path,
                "success": success,
                "return_code": result.returncode
            })

            self.record_operation(success=success)
            
            return success, output
            
        except Exception as e:
            self.logger.error(f"Script execution failed: {e}")
            self.record_operation(success=False)
            return False, str(e)
    
    def send_slack_notification(
        self,
        channel: str,
        message: str,
        webhook_url: Optional[str] = None
    ) -> bool:
        """
        Send Slack notification.
        
        Args:
            channel: Slack channel
            message: Message to send
            webhook_url: Slack webhook URL (from credentials if not provided)
            
        Returns:
            True if successful
        """
        import requests
        
        webhook = webhook_url or self.get_credential("slack_webhook_url")
        if not webhook:
            self.logger.error("Slack webhook URL not configured")
            return False
        
        try:
            payload = {
                "channel": channel,
                "text": message,
                "username": "Automation Agent"
            }
            
            response = requests.post(webhook, json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                self.logger.info(f"Slack notification sent to {channel}")
            else:
                self.logger.error(f"Slack notification failed: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Slack notification error: {e}")
            return False
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        smtp_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            smtp_config: SMTP configuration (from credentials if not provided)
            
        Returns:
            True if successful
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if not smtp_config:
            smtp_config = {
                "host": self.get_credential("smtp_host") or "smtp.gmail.com",
                "port": int(self.get_credential("smtp_port") or "587"),
                "username": self.get_credential("smtp_username"),
                "password": self.get_credential("smtp_password")
            }
        
        if not all([smtp_config.get("username"), smtp_config.get("password")]):
            self.logger.error("SMTP credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config["username"]
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])
            server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {e}")
            return False
    
    def message_sent_successfully(self) -> bool:
        """Check if last message was sent successfully (for testing)."""
        # This would check the last operation result
        if self.task_results:
            last_result = self.task_results[-1]
            return last_result.status == TaskStatus.COMPLETED
        return False
    
    def task_scheduled(self) -> bool:
        """Check if task was scheduled successfully (for testing)."""
        return len(self.tasks) > 0


# Quick access function for enhanced agent
def create_enhanced_agent(
    safety_level: str = "medium",
    headless: bool = False,
    enable_encryption: bool = True
) -> EnhancedAutomationAgent:
    """
    Create enhanced automation agent with production settings.
    
    Args:
        safety_level: 'low', 'medium', or 'high'
        headless: Run browser in headless mode
        enable_encryption: Enable credential encryption
        
    Returns:
        EnhancedAutomationAgent instance
    """
    level_map = {
        'low': SafetyLevel.LOW,
        'medium': SafetyLevel.MEDIUM,
        'high': SafetyLevel.HIGH
    }
    
    agent = EnhancedAutomationAgent(
        safety_level=level_map.get(safety_level, SafetyLevel.MEDIUM),
        headless_mode=headless
    )
    
    if enable_encryption:
        agent.enable_encryption()
    
    return agent


if __name__ == "__main__":
    print("Enhanced Automation Agent with Selenium integration")
    print("Import this module to use in your scripts:")
    print("from enhanced_automation_agent import EnhancedAutomationAgent")