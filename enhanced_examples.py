#!/usr/bin/env python3
"""
Enhanced Automation Agent Examples
Demonstrates advanced features: Selenium, bulk operations, performance monitoring, production deployment
"""

import time
import json
from datetime import datetime

try:
    from enhanced_automation_agent import (
        EnhancedAutomationAgent, BulkOperationConfig, create_enhanced_agent
    )
    from automation_agent import AutomationTask, SafetyLevel
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure enhanced_automation_agent.py is in the same directory")
    exit(1)


# ==================== EXAMPLE 1: Production-Ready Setup ====================
def example_production_setup():
    """Example: Initialize production-ready automation agent."""
    print("\n=== Example 1: Production-Ready Setup ===")
    
    # Create enhanced agent with production settings
    agent = create_enhanced_agent(
        safety_level="medium",
        headless=False,  # Set to True for headless operation
        enable_encryption=True
    )
    
    # Set credentials securely
    agent.set_credentials({
        "slack_webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "smtp_username": "your-email@gmail.com",
        "smtp_password": "your-app-password",
        "chrome_profile_path": "/path/to/chrome/profile"
    })
    
    # Start performance monitoring
    agent.start_performance_monitoring()
    
    print(f"Agent initialized with monitoring")
    print(f"Performance stats: {agent.get_performance_stats()}")
    
    return agent


# ==================== EXAMPLE 2: Enhanced WhatsApp with Selenium ====================
def example_enhanced_whatsapp():
    """Example: Advanced WhatsApp automation with Selenium."""
    print("\n=== Example 2: Enhanced WhatsApp Automation ===")
    
    agent = create_enhanced_agent(headless=False)
    
    # Single message with delivery confirmation
    print("Sending WhatsApp message with delivery confirmation...")
    
    success = agent.send_whatsapp_message_selenium(
        phone_number="256701234567",
        message=f"Automated message with timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        wait_for_delivery=True,
        retry_on_failure=True
    )
    
    if success:
        print("✅ WhatsApp message sent successfully!")
    else:
        print("❌ WhatsApp message failed")
    
    # Schedule recurring messages
    print("\nScheduling recurring WhatsApp messages...")
    
    task_id1 = agent.schedule_whatsapp(
        time_str="09:00",
        phone_number="256701234567",
        message="Daily morning greeting! 🌅",
        repeat_days=["monday", "tuesday", "wednesday", "thursday", "friday"]
    )
    
    task_id2 = agent.schedule_whatsapp(
        time_str="17:00",
        phone_number="256701234567",
        message="Daily evening check-in! 🌆"
    )
    
    print(f"✅ Scheduled tasks: {task_id1}, {task_id2}")
    
    return agent


# ==================== EXAMPLE 3: Bulk WhatsApp Operations ====================
def example_bulk_operations():
    """Example: Bulk WhatsApp operations with rate limiting."""
    print("\n=== Example 3: Bulk WhatsApp Operations ===")
    
    agent = create_enhanced_agent(headless=True)  # Use headless for bulk operations
    
    # Define contacts with personalized messages
    contacts = [
        {
            "phone": "256701234567",
            "name": "John Doe",
            "message": "Hello John! Your personalized greeting from the Automation Agent 🤖"
        },
        {
            "phone": "256709876543", 
            "name": "Jane Smith",
            "message": "Hi Jane! Your automated notification system is working perfectly! ✨"
        },
        {
            "phone": "256712345678",
            "name": "Robert Johnson", 
            "message": "Hey Robert! This is a test of the bulk messaging system."
        }
    ]
    
    # Configure bulk operation settings
    bulk_config = BulkOperationConfig(
        max_concurrent=2,
        delay_between_operations=5.0,  # 5 second delay between messages
        retry_attempts=3,
        continue_on_error=True
    )
    
    print(f"Sending messages to {len(contacts)} contacts...")
    
    # Send bulk messages
    results = agent.send_bulk_messages(contacts, bulk_config)
    
    print(f"\nBulk Operation Results:")
    print(f"  Total contacts: {results['total']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    
    if results['errors']:
        print(f"  Errors: {results['errors']}")
    
    # Get performance stats
    stats = agent.get_performance_stats()
    print(f"\nPerformance Stats:")
    print(f"  Operations: {stats['operations_count']}")
    print(f"  Duration: {stats['duration_seconds']:.2f}s")
    print(f"  Memory usage: {stats['memory_mb']:.2f}MB")
    
    return agent


# ==================== EXAMPLE 4: Website Performance Testing ====================
def example_website_testing():
    """Example: Website performance and health monitoring."""
    print("\n=== Example 4: Website Performance Testing ===")
    
    agent = create_enhanced_agent(headless=True)
    
    # Initialize WebDriver
    if agent.initialize_driver():
        print("✅ WebDriver initialized")
    else:
        print("❌ WebDriver initialization failed")
        return None
    
    # Test multiple websites
    websites = [
        "https://www.google.com",
        "https://www.github.com", 
        "https://www.stackoverflow.com"
    ]
    
    print("\nTesting website performance...")
    
    results = []
    for url in websites:
        print(f"Testing: {url}")
        
        metrics = agent.test_website_performance(
            url=url,
            timeout=30
        )
        
        results.append(metrics)
        
        if metrics["status"] == "success":
            print(f"  ✅ Load time: {metrics['load_time_seconds']}s")
            print(f"  ✅ Title: {metrics.get('title', 'N/A')}")
        else:
            print(f"  ❌ Error: {metrics.get('error', 'Unknown')}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"website_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return agent


# ==================== EXAMPLE 5: Multi-Channel Notifications ====================
def example_notification_system():
    """Example: Send notifications via multiple channels."""
    print("\n=== Example 5: Multi-Channel Notification System ===")
    
    agent = create_enhanced_agent()
    
    # Setup credentials (you'll need to provide real webhook URLs and SMTP credentials)
    print("Setting up notification channels...")
    
    # Note: These are example URLs - replace with real ones
    try:
        # Slack notification
        slack_success = agent.send_slack_notification(
            channel="#alerts",
            message=f"🤖 Automation Alert: System status check completed at {datetime.now().strftime('%H:%M:%S')}"
        )
        
        if slack_success:
            print("✅ Slack notification sent")
        else:
            print("⚠️ Slack notification failed (check webhook URL)")
        
        # Email notification  
        email_success = agent.send_email(
            to_email="admin@example.com",
            subject="Automated Status Report",
            body=f"""
Automation Agent Status Report
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

All systems operational.
Next scheduled tasks running normally.
            """.strip()
        )
        
        if email_success:
            print("✅ Email notification sent")
        else:
            print("⚠️ Email notification failed (check SMTP credentials)")
            
    except Exception as e:
        print(f"⚠️ Notification error: {e}")
        print("Note: Replace webhook URLs and SMTP credentials with real values")
    
    return agent


# ==================== EXAMPLE 6: Comprehensive Workflow Automation ====================
def example_comprehensive_workflow():
    """Example: Complex automation workflow with multiple systems."""
    print("\n=== Example 6: Comprehensive Workflow Automation ===")
    
    agent = create_enhanced_agent(headless=True)
    
    def website_health_check_workflow():
        """Comprehensive website health check workflow."""
        print("🔍 Starting website health check workflow...")
        
        # Test website performance
        metrics = agent.test_website_performance("https://example.com")
        
        # Take screenshot of current state
        screenshot_path = agent.take_screenshot("health_check.png")
        
        # Send notification based on results
        if metrics["status"] == "success":
            status_msg = f"✅ Website health check passed - Load time: {metrics['load_time_seconds']}s"
        else:
            status_msg = f"❌ Website health check failed - Error: {metrics.get('error', 'Unknown')}"
        
        # Log the workflow step
        agent.logger.info(f"Health check workflow completed: {status_msg}")
        
        return {
            "status": metrics["status"],
            "load_time": metrics.get("load_time_seconds"),
            "screenshot": screenshot_path,
            "message": status_msg
        }
    
    def data_backup_workflow():
        """Automated data backup workflow."""
        print("💾 Starting backup workflow...")
        
        # Simulate backup script execution
        success, output = agent.run_script("/path/to/backup_script.sh")
        
        if success:
            agent.logger.info("Backup completed successfully")
            status = "success"
        else:
            agent.logger.error(f"Backup failed: {output}")
            status = "failed"
        
        # Send notification
        agent.send_slack_notification(
            "#alerts", 
            f"Data backup workflow {status} at {datetime.now().strftime('%H:%M:%S')}"
        )
        
        return {
            "status": status,
            "output": output
        }
    
    # Schedule workflows
    print("📅 Scheduling automated workflows...")
    
    # Schedule website health check for weekdays at 8 AM
    health_check_task = AutomationTask(
        name="Website Health Check",
        function=website_health_check_workflow,
        schedule_type="weekly",
        schedule_time="monday 08:00"
    )
    
    # Schedule daily backup at 10 PM
    backup_task = AutomationTask(
        name="Daily Backup",
        function=data_backup_workflow,
        schedule_type="daily",
        schedule_time="22:00"
    )
    
    # Add tasks to agent
    health_task_id = agent.add_task(health_check_task)
    backup_task_id = agent.add_task(backup_task)
    
    print(f"✅ Workflows scheduled:")
    print(f"  Health Check: {health_task_id}")
    print(f"  Backup: {backup_task_id}")
    
    # Run one workflow immediately for demonstration
    print("\n🔄 Running health check workflow immediately...")
    result = agent.run_task(health_task_id)
    
    if result.status.value == "completed":
        print("✅ Health check workflow completed successfully")
    else:
        print(f"❌ Health check workflow failed: {result.error}")
    
    return agent


# ==================== EXAMPLE 7: Error Handling & Recovery ====================
def example_error_handling():
    """Example: Advanced error handling and recovery."""
    print("\n=== Example 7: Error Handling & Recovery ===")
    
    agent = create_enhanced_agent(headless=True)
    
    def robust_whatsapp_workflow():
        """Robust WhatsApp workflow with comprehensive error handling."""
        attempts = 0
        max_attempts = 5
        
        while attempts < max_attempts:
            try:
                print(f"Attempt {attempts + 1}/{max_attempts}")
                
                # Initialize driver if needed
                if not agent.driver_initialized:
                    if not agent.initialize_driver():
                        raise Exception("Failed to initialize WebDriver")
                
                # Attempt WhatsApp operation
                success = agent.send_whatsapp_message_selenium(
                    phone_number="256701234567",
                    message=f"Test message - Attempt {attempts + 1}",
                    wait_for_delivery=True
                )
                
                if success:
                    print("✅ WhatsApp operation successful")
                    return {"status": "success", "attempts": attempts + 1}
                else:
                    raise Exception("WhatsApp operation failed")
                    
            except TimeoutError as e:
                print(f"⚠️ Timeout error: {e}")
                attempts += 1
                time.sleep(10)  # Wait before retry
                
            except Exception as e:
                print(f"❌ Error: {e}")
                
                # Take diagnostic screenshot
                screenshot_path = agent.take_screenshot("error_diagnostic.png")
                
                # Send error notification
                agent.send_slack_notification(
                    "#alerts",
                    f"❌ WhatsApp automation error: {str(e)} at {datetime.now().strftime('%H:%M:%S')}"
                )
                
                attempts += 1
                time.sleep(5)  # Wait before retry
        
        print(f"❌ All {max_attempts} attempts failed")
        return {"status": "failed", "error": "Max attempts exceeded"}
    
    # Run robust workflow
    result = robust_whatsapp_workflow()
    print(f"Final result: {result}")
    
    return agent


# ==================== EXAMPLE 8: Performance Optimization ====================
def example_performance_optimization():
    """Example: Performance monitoring and optimization."""
    print("\n=== Example 8: Performance Optimization ===")
    
    agent = create_enhanced_agent(headless=True)
    
    # Start comprehensive performance monitoring
    agent.start_performance_monitoring()
    
    print("Running performance-intensive operations...")
    
    operations_count = 0
    
    # Simulate multiple operations
    for i in range(10):
        try:
            # Take screenshot
            screenshot = agent.take_screenshot(f"perf_test_{i}.png")
            operations_count += 1
            
            # Simulate processing time
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Operation {i} failed: {e}")
    
    # Stop monitoring and get final stats
    agent.stop_performance_monitoring()
    stats = agent.get_performance_stats()
    
    print(f"\n📊 Performance Results:")
    print(f"  Operations completed: {stats['operations_count']}")
    print(f"  Total duration: {stats['duration_seconds']:.2f}s")
    print(f"  Average operation time: {stats['duration_seconds']/max(operations_count, 1):.3f}s")
    print(f"  Peak memory usage: {stats['memory_mb']:.2f}MB")
    print(f"  Average CPU usage: {stats['cpu_percent']:.1f}%")
    
    # Performance insights
    if stats['duration_seconds'] > 30:
        print("⚠️ Operations taking longer than expected - consider optimization")
    
    if stats['memory_mb'] > 500:
        print("⚠️ High memory usage - consider memory optimization")
    
    return agent


# ==================== EXAMPLE 9: Testing Framework Integration ====================
def example_testing_framework():
    """Example: Automated testing with assertions."""
    print("\n=== Example 9: Testing Framework Integration ===")
    
    agent = create_enhanced_agent(headless=True)
    
    def test_messaging():
        """Test WhatsApp messaging functionality."""
        print("🧪 Testing WhatsApp messaging...")
        
        # Note: This is a test - use a test number in production
        success = agent.send_whatsapp_message_selenium(
            phone_number="256701234567",
            message="Test message for automation testing",
            wait_for_delivery=True
        )
        
        assert success, "WhatsApp messaging test failed"
        assert agent.message_sent_successfully(), "Message not sent successfully"
        
        print("✅ WhatsApp messaging test passed")
        return True
    
    def test_scheduling():
        """Test task scheduling functionality."""
        print("🧪 Testing task scheduling...")
        
        # Create test task
        test_task = AutomationTask(
            name="Test Scheduled Task",
            function=lambda: print("Test execution"),
            schedule_type="daily",
            schedule_time="12:00"
        )
        
        task_id = agent.add_task(test_task)
        
        assert task_id, "Task scheduling failed"
        assert agent.task_scheduled(), "Task not scheduled properly"
        
        print("✅ Task scheduling test passed")
        return True
    
    def test_performance():
        """Test performance monitoring."""
        print("🧪 Testing performance monitoring...")
        
        agent.start_performance_monitoring()
        time.sleep(1)  # Minimal operation
        stats = agent.get_performance_stats()
        
        assert "start_time" in stats, "Performance monitoring not working"
        assert stats["duration_seconds"] > 0, "Duration not recorded"
        
        agent.stop_performance_monitoring()
        print("✅ Performance monitoring test passed")
        return True
    
    # Run all tests
    tests = [
        ("Messaging", test_messaging),
        ("Scheduling", test_scheduling), 
        ("Performance", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name} test...")
            result = test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, "FAILED"))
    
    # Summary
    print(f"\n📋 Test Summary:")
    for test_name, status in results:
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"  {status_icon} {test_name}: {status}")
    
    passed = sum(1 for _, status in results if status == "PASSED")
    print(f"\nResult: {passed}/{len(results)} tests passed")
    
    return agent


# ==================== MAIN DEMO ====================
def run_enhanced_examples():
    """Run all enhanced examples."""
    print("🚀 Enhanced Automation Agent - Advanced Examples")
    print("=" * 60)
    
    examples = [
        ("Production Setup", example_production_setup),
        ("Enhanced WhatsApp", example_enhanced_whatsapp),
        ("Bulk Operations", example_bulk_operations),
        ("Website Testing", example_website_testing),
        ("Notification System", example_notification_system),
        ("Comprehensive Workflow", example_comprehensive_workflow),
        ("Error Handling", example_error_handling),
        ("Performance Optimization", example_performance_optimization),
        ("Testing Framework", example_testing_framework)
    ]
    
    agent = None
    
    print("\nSelect example to run:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i:2}. {name}")
    print("a. Run all examples")
    print("q. Quit")
    
    choice = input("\nEnter your choice: ").strip().lower()
    
    if choice == "a":
        print("\nRunning all examples...")
        for name, example_func in examples:
            print(f"\n{'='*20} {name} {'='*20}")
            try:
                agent = example_func()
                if agent:
                    time.sleep(2)  # Brief pause between examples
            except Exception as e:
                print(f"Example failed: {e}")
    elif choice == "q":
        print("Goodbye!")
        return
    else:
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(examples):
                name, example_func = examples[choice_num - 1]
                print(f"\n{'='*20} {name} {'='*20}")
                agent = example_func()
            else:
                print("Invalid choice!")
        except ValueError:
            print("Invalid input!")
    
    # Cleanup
    if agent:
        agent.cleanup()
        print("\n🧹 Agent cleaned up")


if __name__ == "__main__":
    run_enhanced_examples()