#!/usr/bin/env python3
"""
AI Automation Agent - Complete Computer Control and Task Automation
A comprehensive automation framework for controlling mouse, keyboard, applications, and scheduling tasks.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import signal

# Third-party imports
try:
    import pyautogui
except ImportError:
    print("ERROR: pyautogui is required. Install with: pip install pyautogui")
    sys.exit(1)

try:
    import schedule
except ImportError:
    print("ERROR: schedule is required. Install with: pip install schedule")
    sys.exit(1)

try:
    from PIL import Image, ImageGrab
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    print("WARNING: keyboard module not installed. Some features may be limited.")
    keyboard = None

try:
    import psutil
except ImportError:
    print("WARNING: psutil not installed. Process management features limited.")
    psutil = None


def load_pywhatkit():
    """Safely import pywhatkit with clear guidance when missing."""
    try:
        import pywhatkit as kit  # type: ignore
        return kit
    except ImportError as exc:
        raise ImportError(
            "pywhatkit is required for WhatsApp automation. Install it with: pip install pywhatkit"
        ) from exc


# Configure PyAutoGUI safety
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.5  # Default pause between actions


class TaskStatus(Enum):
    """Status of automated tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SafetyLevel(Enum):
    """Safety levels for automation."""
    LOW = 1  # Minimal safety checks
    MEDIUM = 2  # Standard safety checks
    HIGH = 3  # Maximum safety with confirmations


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    output: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
            "output": self.output
        }


@dataclass
class AutomationTask:
    """Represents an automation task."""
    name: str
    function: Callable
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    schedule_type: Optional[str] = None  # 'daily', 'weekly', 'interval', 'once'
    schedule_time: Optional[str] = None  # e.g., "09:00" for daily
    interval_seconds: Optional[int] = None
    enabled: bool = True
    task_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate task ID if not provided."""
        if not self.task_id:
            self.task_id = f"{self.name}_{int(time.time() * 1000)}"


class AutomationAgent:
    """
    Comprehensive AI Automation Agent for computer control and task automation.
    
    Features:
    - Mouse and keyboard control
    - Screen monitoring and image recognition
    - Application control
    - Task scheduling
    - WhatsApp automation
    - Safety mechanisms and logging
    - Multi-threading support
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM,
        log_level: int = logging.INFO
    ):
        """
        Initialize the automation agent.
        
        Args:
            config_path: Path to configuration file
            safety_level: Safety level for automation
            log_level: Logging level
        """
        self.safety_level = safety_level
        self.config_path = config_path or "automation_config.json"
        self.config: Dict[str, Any] = {}
        self.tasks: Dict[str, AutomationTask] = {}
        self.task_results: List[TaskResult] = []
        self.emergency_stop = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_running = False
        
        # Setup logging
        self._setup_logging(log_level)
        
        # Load configuration
        self._load_config()
        
        # Setup emergency stop
        self._setup_emergency_stop()
        
        self.logger.info("Automation Agent initialized")
    
    def _setup_logging(self, log_level: int):
        """Setup logging system."""
        log_dir = Path("automation_logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"automation_{timestamp}.log"
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized. Log file: {log_file}")
    
    def _setup_emergency_stop(self):
        """Setup emergency stop mechanism."""
        def signal_handler(sig, frame):
            self.logger.warning("Emergency stop triggered!")
            self.emergency_stop = True
            self.stop_scheduler()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        self.logger.info("Emergency stop configured (Ctrl+C)")
    
    def _load_config(self):
        """Load configuration from file."""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
                self.config = {}
        else:
            self.logger.info("No configuration file found, using defaults")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration."""
        self.config = {
            "safety": {
                "failsafe_enabled": True,
                "pause_duration": 0.5,
                "confirmation_required": self.safety_level == SafetyLevel.HIGH
            },
            "whatsapp": {
                "wait_time": 20,
                "close_time": 5,
                "client": "web"
            },
            "screen": {
                "screenshot_dir": "screenshots",
                "monitor_interval": 60
            },
            "notifications": {
                "enabled": True,
                "on_completion": True,
                "on_error": True
            }
        }
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _check_safety(self, action: str) -> bool:
        """
        Check safety before executing action.
        
        Args:
            action: Description of action to perform
            
        Returns:
            True if action is safe to proceed
        """
        if self.emergency_stop:
            self.logger.warning("Emergency stop active, blocking action")
            return False
        
        if self.safety_level == SafetyLevel.HIGH:
            response = input(f"Confirm action: {action} (y/n): ").lower()
            return response == 'y'
        
        return True
    
    def _log_action(self, action: str, details: Dict[str, Any]):
        """Log an action with details."""
        self.logger.info(f"ACTION: {action} | DETAILS: {json.dumps(details)}")
    
    # ================== Mouse Control ==================
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        """
        Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Duration of movement in seconds
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Move mouse to ({x}, {y})"):
            return False
        
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self._log_action("move_mouse", {"x": x, "y": y, "duration": duration})
            return True
        except Exception as e:
            self.logger.error(f"Mouse move failed: {e}")
            return False
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: str = 'left', clicks: int = 1) -> bool:
        """
        Click at coordinates or current position.
        
        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks
            
        Returns:
            True if successful
        """
        position = f"({x}, {y})" if x is not None else "current position"
        if not self._check_safety(f"Click {button} button at {position}"):
            return False
        
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)
            
            self._log_action("click", {
                "x": x, "y": y, "button": button, "clicks": clicks
            })
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Double click at coordinates."""
        return self.click(x, y, clicks=2)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Right click at coordinates."""
        return self.click(x, y, button='right')
    
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 1.0) -> bool:
        """
        Drag from one position to another.
        
        Args:
            x1, y1: Starting coordinates
            x2, y2: Ending coordinates
            duration: Duration of drag
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Drag from ({x1}, {y1}) to ({x2}, {y2})"):
            return False
        
        try:
            pyautogui.moveTo(x1, y1)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration)
            self._log_action("drag", {
                "from": [x1, y1], "to": [x2, y2], "duration": duration
            })
            return True
        except Exception as e:
            self.logger.error(f"Drag failed: {e}")
            return False
    
    def scroll(self, clicks: int, x: Optional[int] = None, 
               y: Optional[int] = None) -> bool:
        """
        Scroll at position.
        
        Args:
            clicks: Amount to scroll (positive = up, negative = down)
            x, y: Coordinates to scroll at
            
        Returns:
            True if successful
        """
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.scroll(clicks)
            self._log_action("scroll", {"clicks": clicks, "x": x, "y": y})
            return True
        except Exception as e:
            self.logger.error(f"Scroll failed: {e}")
            return False
    
    # ================== Keyboard Control ==================
    
    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """
        Type text with keyboard.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Type text: {text[:50]}..."):
            return False
        
        try:
            pyautogui.write(text, interval=interval)
            self._log_action("type_text", {
                "length": len(text), "interval": interval
            })
            return True
        except Exception as e:
            self.logger.error(f"Type text failed: {e}")
            return False
    
    def press_key(self, key: str, presses: int = 1) -> bool:
        """
        Press a key.
        
        Args:
            key: Key name (e.g., 'enter', 'tab', 'a')
            presses: Number of times to press
            
        Returns:
            True if successful
        """
        try:
            pyautogui.press(key, presses=presses)
            self._log_action("press_key", {"key": key, "presses": presses})
            return True
        except Exception as e:
            self.logger.error(f"Press key failed: {e}")
            return False
    
    def hotkey(self, *keys: str) -> bool:
        """
        Press hotkey combination.
        
        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Press hotkey: {'+'.join(keys)}"):
            return False
        
        try:
            pyautogui.hotkey(*keys)
            self._log_action("hotkey", {"keys": list(keys)})
            return True
        except Exception as e:
            self.logger.error(f"Hotkey failed: {e}")
            return False
    
    def copy(self) -> bool:
        """Copy selected content."""
        return self.hotkey('command' if sys.platform == 'darwin' else 'ctrl', 'c')
    
    def paste(self) -> bool:
        """Paste clipboard content."""
        return self.hotkey('command' if sys.platform == 'darwin' else 'ctrl', 'v')
    
    def select_all(self) -> bool:
        """Select all content."""
        return self.hotkey('command' if sys.platform == 'darwin' else 'ctrl', 'a')
    
    # ================== Screen Operations ==================
    
    def take_screenshot(self, filename: Optional[str] = None, 
                       region: Optional[Tuple[int, int, int, int]] = None) -> Optional[str]:
        """
        Take screenshot.
        
        Args:
            filename: Output filename (auto-generated if None)
            region: (left, top, width, height) for partial screenshot
            
        Returns:
            Path to screenshot file
        """
        try:
            screenshot_dir = Path(self.config.get("screen", {}).get(
                "screenshot_dir", "screenshots"
            ))
            screenshot_dir.mkdir(exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = screenshot_dir / filename
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(str(filepath))
            self._log_action("screenshot", {"file": str(filepath), "region": region})
            self.logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None
    
    def find_image_on_screen(self, image_path: str, 
                            confidence: float = 0.9) -> Optional[Tuple[int, int]]:
        """
        Find image on screen.
        
        Args:
            image_path: Path to image to find
            confidence: Match confidence (0-1)
            
        Returns:
            (x, y) coordinates of center, or None
        """
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                self._log_action("find_image", {
                    "image": image_path,
                    "found": True,
                    "position": [center.x, center.y]
                })
                return (center.x, center.y)
            
            self.logger.info(f"Image not found: {image_path}")
            return None
        except Exception as e:
            self.logger.error(f"Image search failed: {e}")
            return None
    
    def click_image(self, image_path: str, confidence: float = 0.9) -> bool:
        """
        Find and click image on screen.
        
        Args:
            image_path: Path to image to find and click
            confidence: Match confidence (0-1)
            
        Returns:
            True if found and clicked
        """
        position = self.find_image_on_screen(image_path, confidence)
        if position:
            return self.click(position[0], position[1])
        return False
    
    def wait_for_image(self, image_path: str, timeout: int = 30,
                      check_interval: float = 1.0) -> Optional[Tuple[int, int]]:
        """
        Wait for image to appear on screen.
        
        Args:
            image_path: Path to image to wait for
            timeout: Maximum wait time in seconds
            check_interval: Interval between checks
            
        Returns:
            (x, y) coordinates when found, or None
        """
        self.logger.info(f"Waiting for image: {image_path} (timeout: {timeout}s)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.emergency_stop:
                return None
            
            position = self.find_image_on_screen(image_path)
            if position:
                return position
            
            time.sleep(check_interval)
        
        self.logger.warning(f"Image not found within timeout: {image_path}")
        return None
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen size."""
        size = pyautogui.size()
        return (size.width, size.height)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        pos = pyautogui.position()
        return (pos.x, pos.y)
    
    # ================== Application Control ==================
    
    def open_application(self, app_name: str, wait_time: float = 2.0) -> bool:
        """
        Open application by name.
        
        Args:
            app_name: Application name or path
            wait_time: Time to wait after opening
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Open application: {app_name}"):
            return False
        
        try:
            if sys.platform == 'darwin':  # macOS
                os.system(f'open -a "{app_name}"')
            elif sys.platform == 'win32':  # Windows
                os.system(f'start "" "{app_name}"')
            else:  # Linux
                os.system(f'{app_name} &')
            
            time.sleep(wait_time)
            self._log_action("open_application", {
                "app": app_name, "wait_time": wait_time
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to open application: {e}")
            return False
    
    def close_application(self, app_name: str) -> bool:
        """
        Close application by name.
        
        Args:
            app_name: Application name
            
        Returns:
            True if successful
        """
        if not psutil:
            self.logger.warning("psutil not available, cannot close application")
            return False
        
        if not self._check_safety(f"Close application: {app_name}"):
            return False
        
        try:
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    self._log_action("close_application", {"app": app_name})
                    return True
            
            self.logger.warning(f"Application not found: {app_name}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to close application: {e}")
            return False
    
    # ================== WhatsApp Automation ==================
    
    def send_whatsapp_message(self, phone: str, message: str,
                             wait_time: Optional[int] = None,
                             close_time: Optional[int] = None) -> bool:
        """
        Send WhatsApp message via WhatsApp Web.
        
        Args:
            phone: Phone number in international format
            message: Message to send
            wait_time: Seconds to wait for WhatsApp Web to load
            close_time: Seconds before closing tab
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Send WhatsApp to {phone}"):
            return False
        
        try:
            kit = load_pywhatkit()

            wait = wait_time or self.config.get("whatsapp", {}).get("wait_time", 20)
            close = close_time or self.config.get("whatsapp", {}).get("close_time", 5)

            kit.sendwhatmsg_instantly(
                phone, message,
                wait_time=wait,
                tab_close=True,
                close_time=close
            )
            
            self._log_action("whatsapp_message", {
                "phone": phone[:5] + "***",  # Partial phone for privacy
                "message_length": len(message)
            })
            return True
        except Exception as e:
            self.logger.error(f"WhatsApp message failed: {e}")
            return False
    
    def send_whatsapp_to_group(self, group_id: str, message: str,
                               wait_time: Optional[int] = None,
                               close_time: Optional[int] = None) -> bool:
        """
        Send WhatsApp message to group.
        
        Args:
            group_id: WhatsApp Web group ID
            message: Message to send
            wait_time: Seconds to wait for WhatsApp Web to load
            close_time: Seconds before closing tab
            
        Returns:
            True if successful
        """
        if not self._check_safety(f"Send WhatsApp to group {group_id}"):
            return False
        
        try:
            kit = load_pywhatkit()

            wait = wait_time or self.config.get("whatsapp", {}).get("wait_time", 20)
            close = close_time or self.config.get("whatsapp", {}).get("close_time", 5)

            kit.sendwhatmsg_to_group_instantly(
                group_id, message,
                wait_time=wait,
                tab_close=True,
                close_time=close
            )
            
            self._log_action("whatsapp_group_message", {
                "group_id": group_id[:10] + "...",
                "message_length": len(message)
            })
            return True
        except Exception as e:
            self.logger.error(f"WhatsApp group message failed: {e}")
            return False
    
    # ================== Task Scheduling ==================
    
    def add_task(self, task: AutomationTask) -> str:
        """
        Add automation task.
        
        Args:
            task: AutomationTask to add
            
        Returns:
            Task ID
        """
        self.tasks[task.task_id] = task
        self.logger.info(f"Task added: {task.name} (ID: {task.task_id})")
        
        # Schedule if needed
        if task.schedule_type and task.enabled:
            self._schedule_task(task)
        
        return task.task_id
    
    def _schedule_task(self, task: AutomationTask):
        """Schedule a task based on its configuration."""
        if task.schedule_type == 'daily' and task.schedule_time:
            schedule.every().day.at(task.schedule_time).do(
                self._execute_task, task.task_id
            )
            self.logger.info(f"Scheduled daily task: {task.name} at {task.schedule_time}")
        
        elif task.schedule_type == 'weekly' and task.schedule_time:
            # Format: "monday 09:00"
            day, time_str = task.schedule_time.split()
            getattr(schedule.every(), day.lower()).at(time_str).do(
                self._execute_task, task.task_id
            )
            self.logger.info(f"Scheduled weekly task: {task.name} on {day} at {time_str}")
        
        elif task.schedule_type == 'interval' and task.interval_seconds:
            schedule.every(task.interval_seconds).seconds.do(
                self._execute_task, task.task_id
            )
            self.logger.info(f"Scheduled interval task: {task.name} every {task.interval_seconds}s")
    
    def _execute_task(self, task_id: str) -> TaskResult:
        """Execute a task and return result."""
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Task not found: {task_id}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                start_time=datetime.now(),
                error="Task not found"
            )
        
        self.logger.info(f"Executing task: {task.name}")
        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            output = task.function(*task.args, **task.kwargs)
            result.status = TaskStatus.COMPLETED
            result.output = output
            self.logger.info(f"Task completed: {task.name}")
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            self.logger.error(f"Task failed: {task.name} - {e}")
            self.logger.debug(traceback.format_exc())
        finally:
            result.end_time = datetime.now()
            self.task_results.append(result)
        
        # Notifications
        if self.config.get("notifications", {}).get("enabled"):
            self._send_notification(result)
        
        return result
    
    def run_task(self, task_id: str) -> TaskResult:
        """
        Run a task immediately.
        
        Args:
            task_id: Task ID to run
            
        Returns:
            TaskResult
        """
        return self._execute_task(task_id)
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.logger.info(f"Task removed: {task_id}")
            return True
        return False
    
    def start_scheduler(self):
        """Start the task scheduler in background thread."""
        if self._scheduler_running:
            self.logger.warning("Scheduler already running")
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def _scheduler_loop(self):
        """Scheduler main loop."""
        while self._scheduler_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
    
    def stop_scheduler(self):
        """Stop the task scheduler."""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        self.logger.info("Scheduler stopped")
    
    # ================== Workflow Chaining ==================
    
    def create_workflow(self, name: str, steps: List[Callable]) -> Callable:
        """
        Create a workflow that chains multiple actions.
        
        Args:
            name: Workflow name
            steps: List of callable functions to execute in order
            
        Returns:
            Callable workflow function
        """
        def workflow(*args, **kwargs):
            self.logger.info(f"Starting workflow: {name}")
            results = []
            
            for i, step in enumerate(steps):
                if self.emergency_stop:
                    self.logger.warning(f"Workflow {name} stopped by emergency stop")
                    break
                
                try:
                    self.logger.info(f"Workflow {name} - Step {i+1}/{len(steps)}")
                    result = step(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Workflow {name} failed at step {i+1}: {e}")
                    raise
            
            self.logger.info(f"Workflow {name} completed")
            return results
        
        workflow.__name__ = name
        return workflow
    
    # ================== Utility Functions ==================
    
    def wait(self, seconds: float):
        """Wait for specified seconds."""
        time.sleep(seconds)
    
    def _send_notification(self, result: TaskResult):
        """Send notification about task result."""
        # For now, just log. Could integrate with system notifications
        if result.status == TaskStatus.COMPLETED:
            if self.config.get("notifications", {}).get("on_completion"):
                self.logger.info(f"NOTIFICATION: Task {result.task_id} completed")
        elif result.status == TaskStatus.FAILED:
            if self.config.get("notifications", {}).get("on_error"):
                self.logger.error(f"NOTIFICATION: Task {result.task_id} failed - {result.error}")
    
    def get_task_results(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get task execution results.
        
        Args:
            task_id: Specific task ID, or None for all results
            
        Returns:
            List of result dictionaries
        """
        if task_id:
            results = [r for r in self.task_results if r.task_id == task_id]
        else:
            results = self.task_results
        
        return [r.to_dict() for r in results]
    
    def save_results(self, filename: str = "task_results.json"):
        """Save task results to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.get_task_results(), f, indent=2)
            self.logger.info(f"Results saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def get_config(self, key: str = None) -> Any:
        """Get configuration value."""
        if key:
            return self.config.get(key)
        return self.config
    
    def set_config(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self._save_config()

    def cleanup(self):
        """Stop schedulers and reset safety flags before shutdown."""
        try:
            self.stop_scheduler()
        except Exception as exc:  # pragma: no cover - defensive guard
            self.logger.error(f"Scheduler cleanup failed: {exc}")
        finally:
            self._scheduler_thread = None
            self._scheduler_running = False
            self.emergency_stop = False
            self.logger.info("Automation agent cleanup complete")


# Quick access functions
def create_agent(safety_level: str = "medium") -> AutomationAgent:
    """
    Create automation agent with specified safety level.
    
    Args:
        safety_level: 'low', 'medium', or 'high'
        
    Returns:
        AutomationAgent instance
    """
    level_map = {
        'low': SafetyLevel.LOW,
        'medium': SafetyLevel.MEDIUM,
        'high': SafetyLevel.HIGH
    }
    return AutomationAgent(safety_level=level_map.get(safety_level, SafetyLevel.MEDIUM))


if __name__ == "__main__":
    # Example usage
    print("Automation Agent initialized. Import this module to use in your scripts.")
    print("Example: from automation_agent import AutomationAgent")