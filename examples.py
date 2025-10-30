#!/usr/bin/env python3
"""
Automation Agent - Usage Examples
Demonstrates various automation capabilities with real-world examples.
"""

from automation_agent import AutomationAgent, AutomationTask, SafetyLevel
import time
from datetime import datetime


# ==================== EXAMPLE 1: Basic Mouse & Keyboard ====================
def example_basic_controls():
    """Example: Basic mouse and keyboard control."""
    print("\n=== Example 1: Basic Mouse & Keyboard Control ===")
    
    agent = AutomationAgent(safety_level=SafetyLevel.LOW)
    
    # Get screen size
    width, height = agent.get_screen_size()
    print(f"Screen size: {width}x{height}")
    
    # Move mouse to center
    agent.move_mouse(width // 2, height // 2, duration=1.0)
    
    # Type some text (will type where cursor is)
    agent.type_text("Hello from Automation Agent!")
    
    # Press Enter
    agent.press_key('enter')
    
    # Use hotkeys
    agent.hotkey('command', 'a')  # Select all (macOS)
    agent.copy()  # Copy
    
    print("Basic controls example completed!")


# ==================== EXAMPLE 2: WhatsApp Automation ====================
def example_whatsapp_automation():
    """Example: Send WhatsApp message at scheduled time."""
    print("\n=== Example 2: WhatsApp Automation ===")
    
    agent = AutomationAgent()
    
    # Single message
    phone = "+1234567890"  # Replace with actual number
    message = "Hello! This is an automated message from the Automation Agent."
    
    # Uncomment to send immediately
    # agent.send_whatsapp_message(phone, message)
    
    # Schedule daily WhatsApp message at 9 AM
    task = AutomationTask(
        name="Daily WhatsApp Greeting",
        function=agent.send_whatsapp_message,
        args=(phone, "Good morning! This is your daily automated greeting."),
        schedule_type="daily",
        schedule_time="09:00"
    )
    
    task_id = agent.add_task(task)
    print(f"Task scheduled with ID: {task_id}")
    
    # Start scheduler
    agent.start_scheduler()
    print("Scheduler started. Task will run daily at 9 AM.")
    
    # Keep running (in real usage, this would be a long-running process)
    # agent._scheduler_running will be True until stopped
    
    return agent


# ==================== EXAMPLE 3: Screenshot & Image Recognition ====================
def example_screenshot_and_image_search():
    """Example: Take screenshots and find images on screen."""
    print("\n=== Example 3: Screenshot & Image Recognition ===")
    
    agent = AutomationAgent()
    
    # Take full screenshot
    screenshot_path = agent.take_screenshot()
    print(f"Screenshot saved: {screenshot_path}")
    
    # Take screenshot of specific region (left, top, width, height)
    region_screenshot = agent.take_screenshot(
        filename="region_screenshot.png",
        region=(100, 100, 800, 600)
    )
    print(f"Region screenshot saved: {region_screenshot}")
    
    # Schedule hourly screenshots
    task = AutomationTask(
        name="Hourly Screenshot",
        function=agent.take_screenshot,
        schedule_type="interval",
        interval_seconds=3600  # Every hour
    )
    agent.add_task(task)
    
    # Find and click an image (if you have a button image)
    # button_path = "path/to/button.png"
    # if agent.click_image(button_path, confidence=0.8):
    #     print("Button found and clicked!")
    # else:
    #     print("Button not found")
    
    print("Screenshot and image search example completed!")


# ==================== EXAMPLE 4: Application Control ====================
def example_application_control():
    """Example: Open, control, and close applications."""
    print("\n=== Example 4: Application Control ===")
    
    agent = AutomationAgent()
    
    # Open an application (macOS example)
    # agent.open_application("TextEdit")
    # time.sleep(2)
    
    # Type in the application
    # agent.type_text("This is automated text in TextEdit!")
    
    # Save with hotkey
    # agent.hotkey('command', 's')
    # time.sleep(1)
    
    # Type filename
    # agent.type_text("automated_document.txt")
    # agent.press_key('enter')
    
    # Close application
    # time.sleep(2)
    # agent.close_application("TextEdit")
    
    print("Application control example completed!")


# ==================== EXAMPLE 5: Form Automation ====================
def example_form_automation():
    """Example: Fill out forms automatically."""
    print("\n=== Example 5: Form Automation ===")
    
    agent = AutomationAgent()
    
    # Example form data
    form_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "message": "This is an automated message filled by the Automation Agent."
    }
    
    # Open browser to form (example)
    # agent.open_application("Google Chrome")
    # time.sleep(2)
    
    # Navigate to form URL (you'd need to use keyboard to type in address bar)
    # agent.hotkey('command', 'l')  # Focus address bar
    # agent.type_text("https://example.com/form")
    # agent.press_key('enter')
    # time.sleep(3)
    
    # Fill form fields (assuming you're clicking/tabbing through)
    # for field, value in form_data.items():
    #     agent.type_text(value)
    #     agent.press_key('tab')  # Move to next field
    
    # Submit form
    # agent.press_key('enter')
    
    print("Form automation example completed!")


# ==================== EXAMPLE 6: Workflow Chaining ====================
def example_workflow_chaining():
    """Example: Chain multiple actions into a workflow."""
    print("\n=== Example 6: Workflow Chaining ===")
    
    agent = AutomationAgent()
    
    # Define individual steps
    def step1():
        print("Step 1: Taking screenshot...")
        return agent.take_screenshot()
    
    def step2():
        print("Step 2: Moving mouse to center...")
        width, height = agent.get_screen_size()
        return agent.move_mouse(width // 2, height // 2)
    
    def step3():
        print("Step 3: Typing text...")
        return agent.type_text("Workflow completed!")
    
    # Create workflow
    workflow = agent.create_workflow(
        name="Demo Workflow",
        steps=[step1, step2, step3]
    )
    
    # Execute workflow
    results = workflow()
    print(f"Workflow results: {results}")
    
    print("Workflow chaining example completed!")


# ==================== EXAMPLE 7: Scheduled Tasks ====================
def example_scheduled_tasks():
    """Example: Schedule various types of tasks."""
    print("\n=== Example 7: Scheduled Tasks ===")
    
    agent = AutomationAgent()
    
    # Daily task at specific time
    daily_task = AutomationTask(
        name="Daily Report Screenshot",
        function=agent.take_screenshot,
        kwargs={"filename": f"daily_report_{datetime.now().strftime('%Y%m%d')}.png"},
        schedule_type="daily",
        schedule_time="17:00"  # 5 PM
    )
    agent.add_task(daily_task)
    
    # Weekly task
    weekly_task = AutomationTask(
        name="Weekly Backup Reminder",
        function=lambda: print("Time for weekly backup!"),
        schedule_type="weekly",
        schedule_time="monday 09:00"
    )
    agent.add_task(weekly_task)
    
    # Interval task (every 5 minutes)
    interval_task = AutomationTask(
        name="Status Check",
        function=lambda: print(f"Status check at {datetime.now()}"),
        schedule_type="interval",
        interval_seconds=300
    )
    agent.add_task(interval_task)
    
    # Start scheduler
    agent.start_scheduler()
    print("All tasks scheduled!")
    
    # List all tasks
    print("\nScheduled tasks:")
    for task_id, task in agent.tasks.items():
        print(f"  - {task.name} ({task.schedule_type})")
    
    return agent


# ==================== EXAMPLE 8: Screen Monitoring ====================
def example_screen_monitoring():
    """Example: Monitor screen for changes or specific content."""
    print("\n=== Example 8: Screen Monitoring ===")
    
    agent = AutomationAgent()
    
    # Wait for a specific image to appear
    # image_path = "path/to/expected_image.png"
    # print(f"Waiting for image: {image_path}")
    # position = agent.wait_for_image(image_path, timeout=60)
    # 
    # if position:
    #     print(f"Image found at position: {position}")
    #     agent.click(position[0], position[1])
    # else:
    #     print("Image not found within timeout")
    
    # Monitor screen continuously
    def monitor_screen():
        """Take screenshot every minute for monitoring."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return agent.take_screenshot(filename=f"monitor_{timestamp}.png")
    
    monitor_task = AutomationTask(
        name="Screen Monitor",
        function=monitor_screen,
        schedule_type="interval",
        interval_seconds=60
    )
    agent.add_task(monitor_task)
    
    print("Screen monitoring example completed!")


# ==================== EXAMPLE 9: Copy-Paste Between Applications ====================
def example_copy_paste_automation():
    """Example: Copy data from one app and paste to another."""
    print("\n=== Example 9: Copy-Paste Between Applications ===")
    
    agent = AutomationAgent()
    
    # Open first application
    # agent.open_application("Notes")
    # time.sleep(2)
    
    # Select and copy content
    # agent.select_all()
    # agent.copy()
    # print("Copied content from first app")
    
    # Switch to second application
    # agent.hotkey('command', 'tab')  # Switch apps on macOS
    # time.sleep(1)
    
    # Or open specific app
    # agent.open_application("TextEdit")
    # time.sleep(2)
    
    # Paste content
    # agent.paste()
    # print("Pasted content to second app")
    
    # Save
    # agent.hotkey('command', 's')
    
    print("Copy-paste automation example completed!")


# ==================== EXAMPLE 10: Complete WhatsApp Scheduler ====================
def example_whatsapp_scheduler():
    """Example: Complete WhatsApp scheduling system."""
    print("\n=== Example 10: Complete WhatsApp Scheduler ===")
    
    agent = AutomationAgent()
    
    # Define messages to send
    contacts = {
        "+1234567890": {
            "name": "John",
            "messages": {
                "morning": "Good morning John! Have a great day!",
                "evening": "Good evening John! Hope you had a productive day!"
            }
        }
    }
    
    # Schedule morning messages
    for phone, data in contacts.items():
        morning_task = AutomationTask(
            name=f"Morning message to {data['name']}",
            function=agent.send_whatsapp_message,
            args=(phone, data['messages']['morning']),
            schedule_type="daily",
            schedule_time="09:00"
        )
        agent.add_task(morning_task)
    
    # Schedule evening messages
    for phone, data in contacts.items():
        evening_task = AutomationTask(
            name=f"Evening message to {data['name']}",
            function=agent.send_whatsapp_message,
            args=(phone, data['messages']['evening']),
            schedule_type="daily",
            schedule_time="18:00"
        )
        agent.add_task(evening_task)
    
    agent.start_scheduler()
    print("WhatsApp scheduler started with morning and evening messages!")
    
    return agent


# ==================== EXAMPLE 11: Advanced Workflow ====================
def example_advanced_workflow():
    """Example: Complex workflow with error handling."""
    print("\n=== Example 11: Advanced Workflow ===")
    
    agent = AutomationAgent()
    
    def safe_step(action_name, action_func):
        """Wrapper for safe step execution."""
        try:
            print(f"Executing: {action_name}")
            result = action_func()
            print(f"✓ {action_name} completed")
            return result
        except Exception as e:
            print(f"✗ {action_name} failed: {e}")
            return None
    
    # Complex workflow
    def complex_workflow():
        steps = [
            ("Open Application", lambda: agent.open_application("Notes")),
            ("Wait", lambda: agent.wait(2)),
            ("Type Content", lambda: agent.type_text("Automated workflow test")),
            ("Save", lambda: agent.hotkey('command', 's')),
            ("Screenshot", lambda: agent.take_screenshot("workflow_result.png"))
        ]
        
        results = []
        for step_name, step_func in steps:
            result = safe_step(step_name, step_func)
            results.append(result)
            if result is False:  # If step failed critically
                print("Workflow aborted due to error")
                break
        
        return results
    
    # Execute workflow
    results = complex_workflow()
    print(f"Workflow completed with {len(results)} steps")


# ==================== MAIN DEMO ====================
def run_all_examples():
    """Run all examples (commented out for safety)."""
    print("=" * 60)
    print("AUTOMATION AGENT - USAGE EXAMPLES")
    print("=" * 60)
    
    # Uncomment examples you want to run
    # WARNING: These will control your mouse and keyboard!
    
    # example_basic_controls()
    # example_whatsapp_automation()
    example_screenshot_and_image_search()
    # example_application_control()
    # example_form_automation()
    example_workflow_chaining()
    example_scheduled_tasks()
    # example_screen_monitoring()
    # example_copy_paste_automation()
    # example_whatsapp_scheduler()
    # example_advanced_workflow()
    
    print("\n" + "=" * 60)
    print("Examples completed! Check the code for more details.")
    print("=" * 60)


if __name__ == "__main__":
    # Display menu
    print("\nAutomation Agent - Example Selector")
    print("=" * 50)
    print("1.  Basic Mouse & Keyboard Control")
    print("2.  WhatsApp Automation")
    print("3.  Screenshot & Image Recognition")
    print("4.  Application Control")
    print("5.  Form Automation")
    print("6.  Workflow Chaining")
    print("7.  Scheduled Tasks")
    print("8.  Screen Monitoring")
    print("9.  Copy-Paste Between Apps")
    print("10. Complete WhatsApp Scheduler")
    print("11. Advanced Workflow")
    print("12. Run Safe Examples")
    print("=" * 50)
    
    choice = input("\nSelect example (1-12) or 'q' to quit: ").strip()
    
    examples_map = {
        "1": example_basic_controls,
        "2": example_whatsapp_automation,
        "3": example_screenshot_and_image_search,
        "4": example_application_control,
        "5": example_form_automation,
        "6": example_workflow_chaining,
        "7": example_scheduled_tasks,
        "8": example_screen_monitoring,
        "9": example_copy_paste_automation,
        "10": example_whatsapp_scheduler,
        "11": example_advanced_workflow,
        "12": run_all_examples
    }
    
    if choice in examples_map:
        examples_map[choice]()
    elif choice.lower() != 'q':
        print("Invalid choice!")