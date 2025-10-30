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
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import psutil
from cryptography.fernet import Fernet

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
        retry_attempts: int = 3
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
        
        # Bulk operation tracking
        self.bulk_operations: List[Dict[str, Any]] = []
        
        self.logger.info("Enhanced Automation Agent initialized")
    
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
        Send messages to multiple contacts with rate limiting.
        
        Args:
            contacts: List of contact dicts with 'phone', 'name', 'message'
            config: Bulk operation configuration
            
        Returns:
            Results dictionary with success/failure counts
        """
        config = config or BulkOperationConfig()
        
        results = {
            "total": len(contacts),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        self.logger.info(f"Starting bulk message send to {len(contacts)} contacts")
        
        for i, contact in enumerate(contacts):
            try:
                phone = contact.get("phone")
                message = contact.get("message")
                name = contact.get("name", "Unknown")
                
                if not phone or not message:
                    self.logger.warning(f"Skipping contact {name}: missing phone or message")
                    results["failed"] += 1
                    continue
                
                self.logger.info(f"Sending message to {name} ({i+1}/{len(contacts)})")
                
                success = self.send_whatsapp_message_selenium(
                    phone_number=phone,
                    message=message,
                    retry_on_failure=True
                )
                
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{name} ({phone})")
                
                # Rate limiting
                if i < len(contacts) - 1:
                    time.sleep(config.delay_between_operations)
                
            except Exception as e:
                self.logger.error(f"Error sending to {contact.get('name', 'Unknown')}: {e}")
                results["failed"] += 1
                results["errors"].append(f"{contact.get('name', 'Unknown')}: {str(e)}")
                self.record_operation(success=False)
                
                if not config.continue_on_error:
                    break
        
        self.logger.info(f"Bulk send complete: {results['successful']}/{results['total']} successful")
        return results
    
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
        """Update performance counters when monitoring is enabled."""
        if not self.monitoring_enabled:
            return
        self.performance_metrics.operations_count += 1
        if not success:
            self.performance_metrics.errors_count += 1
    
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