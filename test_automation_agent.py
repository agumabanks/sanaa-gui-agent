#!/usr/bin/env python3
"""
Test Suite for Automation Agent
Comprehensive tests for all automation functionality.
"""

import unittest
import tempfile
import os
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation_agent import (
    AutomationAgent, AutomationTask, SafetyLevel, TaskStatus, TaskResult
)


class TestAutomationAgent(unittest.TestCase):
    """Test cases for AutomationAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")

        # Create agent with test config
        self.agent = AutomationAgent(
            config_path=self.config_path,
            safety_level=SafetyLevel.LOW  # Use low safety for testing
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Stop any running schedulers
        self.agent.stop_scheduler()

        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test agent initialization."""
        self.assertIsInstance(self.agent, AutomationAgent)
        self.assertEqual(self.agent.safety_level, SafetyLevel.LOW)
        self.assertIsInstance(self.agent.tasks, dict)
        self.assertIsInstance(self.agent.task_results, list)

    def test_config_management(self):
        """Test configuration loading and saving."""
        # Test default config creation
        self.assertIn("safety", self.agent.config)
        self.assertIn("whatsapp", self.agent.config)

        # Test config modification
        self.agent.set_config("test_key", "test_value")
        self.assertEqual(self.agent.get_config("test_key"), "test_value")

        # Test config saving
        self.agent._save_config()
        self.assertTrue(os.path.exists(self.config_path))

    @patch('pyautogui.size')
    def test_screen_size(self, mock_size):
        """Test screen size retrieval."""
        mock_size.return_value = Mock(width=1920, height=1080)
        size = self.agent.get_screen_size()
        self.assertEqual(size, (1920, 1080))

    @patch('pyautogui.position')
    def test_mouse_position(self, mock_position):
        """Test mouse position retrieval."""
        mock_position.return_value = Mock(x=100, y=200)
        pos = self.agent.get_mouse_position()
        self.assertEqual(pos, (100, 200))

    @patch('pyautogui.moveTo')
    def test_mouse_movement(self, mock_move):
        """Test mouse movement."""
        result = self.agent.move_mouse(500, 500)
        self.assertTrue(result)
        mock_move.assert_called_once_with(500, 500, duration=0.5)

    @patch('pyautogui.click')
    def test_mouse_click(self, mock_click):
        """Test mouse clicking."""
        result = self.agent.click(100, 200)
        self.assertTrue(result)
        mock_click.assert_called_once_with(100, 200, clicks=1, button='left')

    @patch('pyautogui.doubleClick')
    def test_double_click(self, mock_double_click):
        """Test double click."""
        with patch('pyautogui.click') as mock_click:
            result = self.agent.double_click(100, 200)
            self.assertTrue(result)
            mock_click.assert_called_once_with(100, 200, clicks=2, button='left')

    @patch('pyautogui.write')
    def test_text_typing(self, mock_write):
        """Test text typing."""
        result = self.agent.type_text("Hello World")
        self.assertTrue(result)
        mock_write.assert_called_once_with("Hello World", interval=0.05)

    @patch('pyautogui.press')
    def test_key_press(self, mock_press):
        """Test key pressing."""
        result = self.agent.press_key('enter')
        self.assertTrue(result)
        mock_press.assert_called_once_with('enter', presses=1)

    @patch('pyautogui.hotkey')
    def test_hotkey(self, mock_hotkey):
        """Test hotkey combinations."""
        result = self.agent.hotkey('ctrl', 'c')
        self.assertTrue(result)
        mock_hotkey.assert_called_once_with('ctrl', 'c')

    @patch('pyautogui.screenshot')
    def test_screenshot(self, mock_screenshot):
        """Test screenshot functionality."""
        mock_screenshot.return_value = Mock()
        mock_screenshot.return_value.save = Mock()

        result = self.agent.take_screenshot("test.png")
        self.assertIsInstance(result, str)
        self.assertIn("test.png", result)

    @patch('pyautogui.locateOnScreen')
    @patch('pyautogui.center')
    def test_image_finding(self, mock_center, mock_locate):
        """Test image finding on screen."""
        mock_locate.return_value = Mock()
        mock_center.return_value = Mock(x=100, y=200)

        result = self.agent.find_image_on_screen("test.png")
        self.assertEqual(result, (100, 200))

    def test_task_creation(self):
        """Test automation task creation."""
        def test_function():
            return "test result"

        task = AutomationTask(
            name="Test Task",
            function=test_function,
            args=(1, 2),
            kwargs={"key": "value"}
        )

        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.args, (1, 2))
        self.assertEqual(task.kwargs, {"key": "value"})
        self.assertIsNotNone(task.task_id)

    def test_task_execution(self):
        """Test task execution."""
        def test_function(x, y):
            return x + y

        task = AutomationTask(
            name="Add Task",
            function=test_function,
            args=(5, 3)
        )

        task_id = self.agent.add_task(task)
        result = self.agent.run_task(task_id)

        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.output, 8)

    def test_task_scheduling(self):
        """Test task scheduling."""
        call_count = 0

        def counting_function():
            nonlocal call_count
            call_count += 1
            return f"Called {call_count} times"

        task = AutomationTask(
            name="Counting Task",
            function=counting_function,
            schedule_type="interval",
            interval_seconds=1
        )

        task_id = self.agent.add_task(task)
        self.agent.start_scheduler()

        # Wait a bit for scheduler to run
        time.sleep(3.5)

        self.agent.stop_scheduler()

        # Should have been called at least 3 times
        self.assertGreaterEqual(call_count, 3)

    def test_workflow_creation(self):
        """Test workflow chaining."""
        results = []

        def step1():
            results.append("step1")
            return "result1"

        def step2():
            results.append("step2")
            return "result2"

        workflow = self.agent.create_workflow("Test Workflow", [step1, step2])
        workflow_results = workflow()

        self.assertEqual(results, ["step1", "step2"])
        self.assertEqual(workflow_results, ["result1", "result2"])

    def test_safety_mechanisms(self):
        """Test safety mechanisms."""
        # Test emergency stop
        self.agent.emergency_stop = True

        # Actions should be blocked
        with patch('pyautogui.moveTo') as mock_move:
            result = self.agent.move_mouse(100, 100)
            self.assertFalse(result)
            mock_move.assert_not_called()

        # Reset for other tests
        self.agent.emergency_stop = False

    def test_error_handling(self):
        """Test error handling in tasks."""
        def failing_function():
            raise ValueError("Test error")

        task = AutomationTask(
            name="Failing Task",
            function=failing_function
        )

        task_id = self.agent.add_task(task)
        result = self.agent.run_task(task_id)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn("Test error", result.error)

    def test_task_results(self):
        """Test task result management."""
        def success_function():
            return "success"

        task = AutomationTask(
            name="Success Task",
            function=success_function
        )

        task_id = self.agent.add_task(task)
        result = self.agent.run_task(task_id)

        # Check results retrieval
        all_results = self.agent.get_task_results()
        self.assertEqual(len(all_results), 1)

        task_results = self.agent.get_task_results(task_id)
        self.assertEqual(len(task_results), 1)
        self.assertEqual(task_results[0]["status"], "completed")

    @patch('automation_agent.load_pywhatkit')
    def test_whatsapp_integration(self, mock_load):
        """Test WhatsApp integration (mocked)."""
        mock_kit = Mock()
        mock_load.return_value = mock_kit

        result = self.agent.send_whatsapp_message("+1234567890", "Test message")
        self.assertTrue(result)

        # Verify the mock was called
        mock_kit.sendwhatmsg_instantly.assert_called_once()

    def test_logging(self):
        """Test logging functionality."""
        with patch('automation_agent.logging') as mock_logging:
            agent = AutomationAgent(safety_level=SafetyLevel.LOW)
            agent.logger.info("Test message")
            mock_logging.getLogger.return_value.info.assert_called_with("Test message")


class TestAutomationTask(unittest.TestCase):
    """Test cases for AutomationTask class."""

    def test_task_initialization(self):
        """Test task initialization."""
        def test_func():
            pass

        task = AutomationTask(
            name="Test Task",
            function=test_func,
            schedule_type="daily",
            schedule_time="09:00"
        )

        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.function, test_func)
        self.assertEqual(task.schedule_type, "daily")
        self.assertEqual(task.schedule_time, "09:00")
        self.assertTrue(task.enabled)
        self.assertIsNotNone(task.task_id)


class TestSafetyLevels(unittest.TestCase):
    """Test cases for safety levels."""

    def test_safety_levels(self):
        """Test safety level enumeration."""
        self.assertEqual(SafetyLevel.LOW.value, 1)
        self.assertEqual(SafetyLevel.MEDIUM.value, 2)
        self.assertEqual(SafetyLevel.HIGH.value, 3)

    def test_safety_level_creation(self):
        """Test agent creation with different safety levels."""
        for level in [SafetyLevel.LOW, SafetyLevel.MEDIUM, SafetyLevel.HIGH]:
            agent = AutomationAgent(safety_level=level)
            self.assertEqual(agent.safety_level, level)


class TestTaskStatus(unittest.TestCase):
    """Test cases for task status."""

    def test_task_status_values(self):
        """Test task status enumeration."""
        self.assertEqual(TaskStatus.PENDING.value, "pending")
        self.assertEqual(TaskStatus.RUNNING.value, "running")
        self.assertEqual(TaskStatus.COMPLETED.value, "completed")
        self.assertEqual(TaskStatus.FAILED.value, "failed")
        self.assertEqual(TaskStatus.CANCELLED.value, "cancelled")


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.agent = AutomationAgent(
            config_path=os.path.join(self.temp_dir, "integration_config.json"),
            safety_level=SafetyLevel.LOW
        )

    def tearDown(self):
        """Clean up integration test fixtures."""
        self.agent.stop_scheduler()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_workflow(self):
        """Test a complete automation workflow."""
        # Create a multi-step workflow
        workflow_results = []

        def step1():
            workflow_results.append("navigation")
            return "navigated"

        def step2():
            workflow_results.append("input")
            return "input_done"

        def step3():
            workflow_results.append("submit")
            return "submitted"

        # Create workflow
        workflow = self.agent.create_workflow("Complete Workflow", [step1, step2, step3])

        # Execute workflow
        results = workflow()

        # Verify execution
        self.assertEqual(workflow_results, ["navigation", "input", "submit"])
        self.assertEqual(results, ["navigated", "input_done", "submitted"])

    def test_scheduled_workflow(self):
        """Test scheduling a workflow."""
        execution_count = 0

        def counting_workflow():
            nonlocal execution_count
            execution_count += 1
            return f"execution_{execution_count}"

        # Create and schedule workflow
        workflow = self.agent.create_workflow("Counting Workflow", [counting_workflow])
        task = AutomationTask(
            name="Scheduled Workflow",
            function=workflow,
            schedule_type="interval",
            interval_seconds=1
        )

        self.agent.add_task(task)
        self.agent.start_scheduler()

        # Wait for multiple executions
        time.sleep(3.5)
        self.agent.stop_scheduler()

        # Verify multiple executions
        self.assertGreaterEqual(execution_count, 3)


class TestConfiguration(unittest.TestCase):
    """Test configuration management."""

    def setUp(self):
        """Set up configuration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config_test.json")

    def tearDown(self):
        """Clean up configuration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_file_operations(self):
        """Test configuration file operations."""
        agent = AutomationAgent(config_path=self.config_path)

        # Modify config
        agent.set_config("test_section", {"key": "value"})
        agent._save_config()

        # Create new agent with same config
        agent2 = AutomationAgent(config_path=self.config_path)

        # Verify config persistence
        self.assertEqual(agent2.get_config("test_section"), {"key": "value"})


# ==================== PERFORMANCE TESTS ====================

class TestPerformance(unittest.TestCase):
    """Performance tests for automation agent."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.agent = AutomationAgent(safety_level=SafetyLevel.LOW)

    def test_mouse_movement_performance(self):
        """Test mouse movement performance."""
        import time

        start_time = time.time()

        # Perform multiple mouse movements
        for i in range(10):
            with patch('pyautogui.moveTo'):
                self.agent.move_mouse(i * 10, i * 10, duration=0.1)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time
        self.assertLess(duration, 2.0)

    def test_task_execution_performance(self):
        """Test task execution performance."""
        import time

        def quick_task():
            return sum(range(1000))

        task = AutomationTask(name="Quick Task", function=quick_task)

        start_time = time.time()

        # Execute multiple tasks
        for _ in range(10):
            self.agent.run_task(self.agent.add_task(task))

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time
        self.assertLess(duration, 5.0)


# ==================== UTILITY FUNCTIONS ====================

def run_specific_test(test_class, test_method):
    """Run a specific test method."""
    suite = unittest.TestSuite()
    suite.addTest(test_class(test_method))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.dirname(__file__), pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\nTest Results:")
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


def create_test_report():
    """Create a test report."""
    import datetime

    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"test_report_{timestamp}.html"

    # Run tests and capture output
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr

    output_buffer = io.StringIO()

    with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
        success = run_all_tests()

    output = output_buffer.getvalue()

    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Automation Agent Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 10px; }}
            .success {{ color: green; }}
            .failure {{ color: red; }}
            .output {{ background-color: #f8f8f8; padding: 10px; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Automation Agent Test Report</h1>
            <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p class="{'success' if success else 'failure'}">
                Status: {'PASSED' if success else 'FAILED'}
            </p>
        </div>
        <div class="output">
            <h2>Test Output</h2>
            {output}
        </div>
    </body>
    </html>
    """

    with open(report_file, 'w') as f:
        f.write(html_content)

    print(f"Test report saved to: {report_file}")
    return report_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Automation Agent Tests")
    parser.add_argument("--report", action="store_true", help="Generate HTML test report")
    parser.add_argument("--specific", nargs=2, metavar=('CLASS', 'METHOD'),
                       help="Run specific test class and method")

    args = parser.parse_args()

    if args.specific:
        test_class, test_method = args.specific
        success = run_specific_test(globals()[test_class], test_method)
    else:
        if args.report:
            create_test_report()
        else:
            success = run_all_tests()

    sys.exit(0 if success else 1)