#!/usr/bin/env python3
"""
Automation Agent Templates
Pre-built templates for common automation workflows.
"""

from automation_agent import AutomationAgent, AutomationTask
from typing import Dict, List, Any, Callable
import json


class AutomationTemplates:
    """Collection of pre-built automation templates."""

    def __init__(self, agent: AutomationAgent):
        self.agent = agent
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.load_builtin_templates()

    def load_builtin_templates(self):
        """Load built-in templates."""
        self.templates = {
            "whatsapp_daily_greeting": {
                "name": "Daily WhatsApp Greeting",
                "description": "Send automated greeting messages via WhatsApp",
                "category": "communication",
                "parameters": {
                    "phone_numbers": ["+1234567890"],
                    "morning_message": "Good morning! Have a great day!",
                    "evening_message": "Good evening! Hope you had a productive day!",
                    "schedule_times": ["09:00", "18:00"]
                },
                "function": self.create_whatsapp_greeting_workflow
            },

            "screenshot_monitor": {
                "name": "Screen Activity Monitor",
                "description": "Take screenshots at regular intervals for monitoring",
                "category": "monitoring",
                "parameters": {
                    "interval_minutes": 60,
                    "max_screenshots": 24,
                    "filename_prefix": "monitor"
                },
                "function": self.create_screenshot_monitor_workflow
            },

            "email_automation": {
                "name": "Email Auto-Responder",
                "description": "Monitor email and send automated responses",
                "category": "communication",
                "parameters": {
                    "check_interval": 300,
                    "response_template": "Thank you for your email. I'll respond shortly.",
                    "keywords": ["urgent", "important"]
                },
                "function": self.create_email_automation_workflow
            },

            "form_filler": {
                "name": "Web Form Auto-Filler",
                "description": "Automatically fill and submit web forms",
                "category": "web",
                "parameters": {
                    "form_url": "https://example.com/form",
                    "field_mappings": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "message": "Automated submission"
                    },
                    "submit_button": "submit"
                },
                "function": self.create_form_filler_workflow
            },

            "data_sync": {
                "name": "Application Data Sync",
                "description": "Copy data between applications automatically",
                "category": "productivity",
                "parameters": {
                    "source_app": "Excel",
                    "target_app": "Google Sheets",
                    "sync_interval": 3600,
                    "data_range": "A1:B10"
                },
                "function": self.create_data_sync_workflow
            },

            "backup_automation": {
                "name": "File Backup Automation",
                "description": "Automatically backup important files",
                "category": "backup",
                "parameters": {
                    "source_dirs": ["/Users/user/Documents"],
                    "backup_dir": "/Users/user/Backup",
                    "schedule": "daily 02:00",
                    "compression": True
                },
                "function": self.create_backup_workflow
            },

            "social_media_poster": {
                "name": "Social Media Auto-Poster",
                "description": "Automatically post content to social media",
                "category": "social",
                "parameters": {
                    "platforms": ["twitter", "facebook"],
                    "content_schedule": "weekly monday 10:00",
                    "content_source": "content_queue.txt"
                },
                "function": self.create_social_media_workflow
            },

            "health_monitor": {
                "name": "System Health Monitor",
                "description": "Monitor system health and send alerts",
                "category": "monitoring",
                "parameters": {
                    "check_interval": 300,
                    "alert_thresholds": {
                        "cpu_percent": 90,
                        "memory_percent": 85,
                        "disk_percent": 95
                    },
                    "alert_email": "admin@example.com"
                },
                "function": self.create_health_monitor_workflow
            }
        }

    def get_template_categories(self) -> List[str]:
        """Get list of template categories."""
        return list(set(template["category"] for template in self.templates.values()))

    def get_templates_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get templates for a specific category."""
        return {k: v for k, v in self.templates.items() if v["category"] == category}

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific template."""
        return self.templates.get(template_id, {})

    def create_task_from_template(self, template_id: str, custom_params: Dict[str, Any] = None) -> str:
        """
        Create a task from a template.

        Args:
            template_id: Template identifier
            custom_params: Custom parameters to override defaults

        Returns:
            Task ID if successful, empty string otherwise
        """
        template = self.get_template(template_id)
        if not template:
            self.agent.logger.error(f"Template not found: {template_id}")
            return ""

        # Merge parameters
        params = template["parameters"].copy()
        if custom_params:
            params.update(custom_params)

        # Create workflow function
        workflow_func = template["function"](params)

        # Create task
        task = AutomationTask(
            name=template["name"],
            function=workflow_func
        )

        # Add to agent
        task_id = self.agent.add_task(task)
        self.agent.logger.info(f"Task created from template: {template['name']}")
        return task_id

    # ==================== TEMPLATE IMPLEMENTATIONS ====================

    def create_whatsapp_greeting_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create WhatsApp greeting workflow."""
        def whatsapp_workflow():
            current_hour = int(self.agent.get_config().get("current_time", "12:00").split(":")[0])

            for phone in params["phone_numbers"]:
                if 6 <= current_hour < 12:  # Morning
                    message = params["morning_message"]
                elif 12 <= current_hour < 18:  # Afternoon
                    message = "Good afternoon! Hope you're having a great day!"
                else:  # Evening
                    message = params["evening_message"]

                self.agent.send_whatsapp_message(phone, message)

        return whatsapp_workflow

    def create_screenshot_monitor_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create screenshot monitoring workflow."""
        screenshot_count = 0
        max_screenshots = params.get("max_screenshots", 24)

        def screenshot_workflow():
            nonlocal screenshot_count
            if screenshot_count >= max_screenshots:
                self.agent.logger.info("Screenshot limit reached")
                return

            timestamp = self.agent.get_config().get("current_time", "unknown").replace(":", "")
            filename = f"{params['filename_prefix']}_{timestamp}_{screenshot_count}.png"

            result = self.agent.take_screenshot(filename)
            if result:
                screenshot_count += 1
                self.agent.logger.info(f"Screenshot {screenshot_count}/{max_screenshots} taken")

        return screenshot_workflow

    def create_email_automation_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create email automation workflow."""
        def email_workflow():
            # This is a placeholder - would need email client integration
            self.agent.logger.info("Email automation workflow executed")
            # In a real implementation, this would:
            # 1. Check email inbox
            # 2. Look for specific keywords
            # 3. Send automated responses
            # 4. Mark emails as processed

        return email_workflow

    def create_form_filler_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create web form filling workflow."""
        def form_workflow():
            try:
                # Open browser and navigate to form
                self.agent.open_application("Google Chrome")
                self.agent.wait(2)

                # Navigate to URL (would need more sophisticated browser automation)
                self.agent.hotkey('ctrl', 'l')  # Focus address bar
                self.agent.type_text(params["form_url"])
                self.agent.press_key('enter')
                self.agent.wait(3)

                # Fill form fields (simplified - would need field detection)
                for field_name, value in params["field_mappings"].items():
                    self.agent.type_text(value)
                    self.agent.press_key('tab')

                # Submit form
                self.agent.press_key('enter')

                self.agent.logger.info("Form submitted successfully")

            except Exception as e:
                self.agent.logger.error(f"Form filling failed: {e}")

        return form_workflow

    def create_data_sync_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create data synchronization workflow."""
        def sync_workflow():
            try:
                # Open source application
                self.agent.open_application(params["source_app"])
                self.agent.wait(3)

                # Select and copy data
                self.agent.hotkey('ctrl', 'a')  # Select all
                self.agent.hotkey('ctrl', 'c')  # Copy
                self.agent.wait(1)

                # Switch to target application
                self.agent.hotkey('alt', 'tab')  # Switch window
                self.agent.wait(1)

                # Paste data
                self.agent.hotkey('ctrl', 'v')  # Paste

                # Save in target application
                self.agent.hotkey('ctrl', 's')
                self.agent.wait(1)

                # Close applications
                self.agent.hotkey('alt', 'f4')  # Close current window
                self.agent.hotkey('alt', 'f4')  # Close other window

                self.agent.logger.info("Data synchronization completed")

            except Exception as e:
                self.agent.logger.error(f"Data sync failed: {e}")

        return sync_workflow

    def create_backup_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create file backup workflow."""
        def backup_workflow():
            import shutil
            from pathlib import Path

            try:
                backup_dir = Path(params["backup_dir"])
                backup_dir.mkdir(exist_ok=True)

                for source_dir in params["source_dirs"]:
                    source_path = Path(source_dir)
                    if source_path.exists():
                        # Create timestamped backup
                        timestamp = self.agent.get_config().get("current_time", "unknown").replace(":", "")
                        backup_name = f"{source_path.name}_backup_{timestamp}"

                        if params.get("compression", False):
                            # Create compressed archive
                            shutil.make_archive(
                                str(backup_dir / backup_name),
                                'zip',
                                source_path
                            )
                        else:
                            # Copy directory
                            shutil.copytree(
                                source_path,
                                backup_dir / backup_name,
                                dirs_exist_ok=True
                            )

                self.agent.logger.info("Backup completed successfully")

            except Exception as e:
                self.agent.logger.error(f"Backup failed: {e}")

        return backup_workflow

    def create_social_media_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create social media posting workflow."""
        def social_workflow():
            # This is a placeholder - would need social media API integrations
            self.agent.logger.info("Social media workflow executed")
            # In a real implementation, this would:
            # 1. Read content from queue
            # 2. Post to specified platforms
            # 3. Handle rate limits and errors
            # 4. Update posting schedule

        return social_workflow

    def create_health_monitor_workflow(self, params: Dict[str, Any]) -> Callable:
        """Create system health monitoring workflow."""
        def health_workflow():
            try:
                import psutil

                # Check system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                alerts = []

                # Check thresholds
                thresholds = params["alert_thresholds"]
                if cpu_percent > thresholds["cpu_percent"]:
                    alerts.append(f"High CPU usage: {cpu_percent}%")

                if memory.percent > thresholds["memory_percent"]:
                    alerts.append(f"High memory usage: {memory.percent}%")

                if disk.percent > thresholds["disk_percent"]:
                    alerts.append(f"Low disk space: {disk.percent}% full")

                if alerts:
                    alert_message = "System Health Alert:\n" + "\n".join(alerts)
                    self.agent.logger.warning(alert_message)

                    # Send alert (would need email integration)
                    # self.send_alert_email(params["alert_email"], alert_message)
                else:
                    self.agent.logger.info("System health check passed")

            except Exception as e:
                self.agent.logger.error(f"Health check failed: {e}")

        return health_workflow

    def save_template(self, template_id: str, template_data: Dict[str, Any]):
        """Save a custom template."""
        self.templates[template_id] = template_data
        self.agent.logger.info(f"Template saved: {template_id}")

    def load_custom_templates(self, filename: str):
        """Load custom templates from file."""
        try:
            with open(filename, 'r') as f:
                custom_templates = json.load(f)
            self.templates.update(custom_templates)
            self.agent.logger.info(f"Custom templates loaded: {len(custom_templates)}")
        except Exception as e:
            self.agent.logger.error(f"Failed to load custom templates: {e}")

    def export_templates(self, filename: str):
        """Export all templates to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.templates, f, indent=2)
            self.agent.logger.info(f"Templates exported to: {filename}")
        except Exception as e:
            self.agent.logger.error(f"Failed to export templates: {e}")


# ==================== TEMPLATE UTILITIES ====================

def create_custom_template(
    name: str,
    description: str,
    category: str,
    parameters: Dict[str, Any],
    workflow_function: Callable
) -> Dict[str, Any]:
    """
    Create a custom template.

    Args:
        name: Template name
        description: Template description
        category: Template category
        parameters: Default parameters
        workflow_function: Function that creates the workflow

    Returns:
        Template dictionary
    """
    return {
        "name": name,
        "description": description,
        "category": category,
        "parameters": parameters,
        "function": workflow_function
    }


def list_available_templates(templates: AutomationTemplates) -> None:
    """List all available templates."""
    print("\nAvailable Automation Templates:")
    print("=" * 50)

    categories = templates.get_template_categories()
    for category in sorted(categories):
        print(f"\n{category.upper()}:")
        category_templates = templates.get_templates_by_category(category)

        for template_id, template in category_templates.items():
            print(f"  • {template['name']}")
            print(f"    {template['description']}")
            print(f"    ID: {template_id}")
            print()


# ==================== EXAMPLE USAGE ====================

def example_template_usage():
    """Example of using templates."""
    from automation_agent import AutomationAgent

    # Create agent
    agent = AutomationAgent()

    # Create template system
    templates = AutomationTemplates(agent)

    # List available templates
    list_available_templates(templates)

    # Create task from template
    task_id = templates.create_task_from_template(
        "whatsapp_daily_greeting",
        custom_params={
            "phone_numbers": ["+1234567890", "+0987654321"],
            "morning_message": "Good morning from Automation Agent!"
        }
    )

    if task_id:
        print(f"Task created with ID: {task_id}")

        # Schedule the task
        task = agent.tasks[task_id]
        task.schedule_type = "daily"
        task.schedule_time = "09:00"

        # Start scheduler
        agent.start_scheduler()
        print("Template-based automation started!")


if __name__ == "__main__":
    example_template_usage()