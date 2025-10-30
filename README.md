# AI Automation Agent - Enhanced Version

A comprehensive Python-based automation framework with advanced features including Selenium WebDriver integration, bulk operations, performance monitoring, and production-ready deployment capabilities.

## ✨ Enhanced Features

### 🚀 Core Enhancements
- **Selenium WebDriver Integration** - Advanced browser automation
- **Automatic ChromeDriver Management** - No manual driver setup required
- **Bulk Operations** - Mass WhatsApp messaging with rate limiting
- **Performance Monitoring** - Real-time system metrics tracking
- **Production Deployment** - Enterprise-grade configuration
- **Security & Encryption** - Secure credential management
- **Multi-Channel Notifications** - Slack, Email, System alerts
- **Advanced Error Handling** - Retry logic and recovery mechanisms

### 🎯 Advanced Capabilities
- **Website Performance Testing** - Load time and availability monitoring
- **Script Execution** - Run external scripts with automation
- **Multi-Session Support** - Multiple browser profiles
- **Credential Encryption** - Fernet encryption for sensitive data
- **Task Retry Logic** - Intelligent retry mechanisms
- **Resource Optimization** - Memory and CPU monitoring
- **Comprehensive Testing** - Automated testing framework integration

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: macOS, Windows, or Linux
- **Chrome Browser**: Latest version recommended
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 500MB free space for dependencies and logs

### Enhanced Dependencies
```
pyautogui>=0.9.53
selenium>=4.15.0
webdriver-manager>=4.0.0
opencv-python>=4.8.0
numpy>=1.24.0
cryptography>=41.0.0
schedule>=1.2.0
Pillow>=9.0.0
psutil>=5.9.0
requests>=2.28.0
pywhatkit>=5.4
plyer>=2.1.0  # Optional: System notifications
```

## 🛠️ Installation

### Quick Installation
```bash
# Clone or download the project
cd automation-agent

# Run enhanced installer
python install.py
```

### Manual Installation
```bash
# Install all dependencies
pip install -r requirements.txt

# Test installation
python -c "from enhanced_automation_agent import EnhancedAutomationAgent; print('Ready!')"
```

### ChromeDriver Setup
- **Automatic**: Handled by `webdriver-manager` (recommended)
- **Manual**: Download from [chromedriver.chromium.org](https://chromedriver.chromium.org/)

## 🚀 Quick Start

### Basic Enhanced Usage
```python
from enhanced_automation_agent import EnhancedAutomationAgent

# Create enhanced agent with production settings
agent = EnhancedAutomationAgent(
    headless_mode=False,
    window_size=(1920, 1080),
    timeout=30,
    retry_attempts=3
)

# Enable security
agent.enable_encryption()
agent.set_credentials({
    "slack_webhook": "YOUR_SLACK_WEBHOOK_URL",
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "your-app-password"
})
```

### Enhanced WhatsApp Automation
```python
# Send message with delivery confirmation
success = agent.send_whatsapp_message_selenium(
    phone_number="256701234567",
    message="Enhanced automation message! 🤖",
    wait_for_delivery=True,
    retry_on_failure=True
)

# Bulk messaging with rate limiting
contacts = [
    {"phone": "256701234567", "name": "John", "message": "Personalized greeting"},
    {"phone": "256709876543", "name": "Jane", "message": "Custom notification"}
]

results = agent.send_bulk_messages(contacts, BulkOperationConfig(
    max_concurrent=2,
    delay_between_operations=5.0
))

# Schedule recurring messages
agent.schedule_whatsapp(
    time_str="09:00",
    phone_number="256701234567", 
    message="Daily morning greeting! 🌅",
    repeat_days=["monday", "tuesday", "wednesday", "thursday", "friday"]
)
```

### Performance Monitoring
```python
# Start comprehensive monitoring
agent.start_performance_monitoring()

# Run operations
agent.move_mouse(500, 500)
agent.click()
agent.take_screenshot()

# Get performance statistics
stats = agent.get_performance_stats()
print(f"Operations: {stats['operations_count']}")
print(f"Duration: {stats['duration_seconds']:.2f}s")
print(f"Memory: {stats['memory_mb']:.2f}MB")
print(f"CPU: {stats['cpu_percent']:.1f}%")
```

### Multi-Channel Notifications
```python
# Slack notification
agent.send_slack_notification(
    channel="#alerts",
    message="🤖 Automation complete! All systems operational."
)

# Email notification
agent.send_email(
    to_email="admin@company.com",
    subject="Daily Automation Report",
    body=f"Automation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
```

### Website Performance Testing
```python
# Test website performance
metrics = agent.test_website_performance(
    url="https://your-website.com",
    timeout=30
)

if metrics["status"] == "success":
    print(f"✅ Load time: {metrics['load_time_seconds']}s")
    print(f"✅ Title: {metrics.get('title', 'N/A')}")
else:
    print(f"❌ Error: {metrics.get('error', 'Unknown')}")
```

## 📖 Enhanced Usage Examples

### Example 1: Production Workflow
```python
from enhanced_automation_agent import create_enhanced_agent

# Create production-ready agent
agent = create_enhanced_agent(
    safety_level="high",
    headless=True,
    enable_encryption=True
)

# Set up monitoring
agent.start_performance_monitoring()

def comprehensive_health_check():
    """Complete system health check workflow."""
    # Test multiple websites
    websites = ["https://site1.com", "https://site2.com"]
    
    results = []
    for url in websites:
        metrics = agent.test_website_performance(url)
        results.append(metrics)
    
    # Take screenshots
    screenshot = agent.take_screenshot("health_status.png")
    
    # Send notification
    if all(r["status"] == "success" for r in results):
        agent.send_slack_notification(
            "#alerts",
            f"✅ All systems healthy at {datetime.now().strftime('%H:%M:%S')}"
        )
    
    return results

# Schedule daily health check
health_task = AutomationTask(
    name="Daily Health Check",
    function=comprehensive_health_check,
    schedule_type="daily",
    schedule_time="08:00"
)

agent.add_task(health_task)
agent.start_scheduler()
```

### Example 2: Bulk WhatsApp Marketing
```python
def bulk_marketing_campaign():
    """Send marketing messages to customer list."""
    
    # Load customer data (example format)
    customers = [
        {"phone": "256701234567", "name": "John", "message": "Hi {name}! New product launch 🎉"},
        {"phone": "256709876543", "name": "Jane", "message": "Hello {name}! Special offer just for you! 🛍️"},
        # ... more customers
    ]
    
    # Personalize messages
    for customer in customers:
        customer["message"] = customer["message"].format(name=customer["name"])
    
    # Configure bulk operation
    config = BulkOperationConfig(
        max_concurrent=3,
        delay_between_operations=8.0,
        retry_attempts=3,
        continue_on_error=True
    )
    
    # Execute bulk messaging
    results = agent.send_bulk_messages(customers, config)
    
    # Report results
    agent.send_email(
        to_email="marketing@company.com",
        subject="Bulk Campaign Results",
        body=f"Campaign completed: {results['successful']}/{results['total']} successful"
    )
    
    return results

# Schedule weekly campaigns
campaign_task = AutomationTask(
    name="Weekly Marketing Campaign",
    function=bulk_marketing_campaign,
    schedule_type="weekly",
    schedule_time="monday 10:00"
)

agent.add_task(campaign_task)
```

### Example 3: Error Recovery and Resilience
```python
def resilient_workflow():
    """Workflow with comprehensive error handling."""
    import time
    
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # Initialize driver if needed
            if not agent.driver_initialized:
                if not agent.initialize_driver():
                    raise Exception("WebDriver initialization failed")
            
            # Attempt operation
            success = agent.send_whatsapp_message_selenium(
                phone_number="256701234567",
                message=f"Resilient workflow - Attempt {attempt + 1}",
                wait_for_delivery=True
            )
            
            if success:
                print("✅ Operation successful")
                return {"status": "success", "attempts": attempt + 1}
            
            raise Exception("Operation returned failure")
            
        except TimeoutError as e:
            print(f"⚠️ Timeout error: {e}")
            attempt += 1
            time.sleep(10)  # Wait before retry
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
            # Take diagnostic screenshot
            agent.take_screenshot("error_diagnostic.png")
            
            # Send error alert
            agent.send_slack_notification(
                "#alerts",
                f"❌ Automation error: {str(e)}"
            )
            
            attempt += 1
            time.sleep(5)  # Wait before retry
    
    print(f"❌ All {max_attempts} attempts failed")
    return {"status": "failed", "error": "Max attempts exceeded"}
```

## 🔧 Configuration

### Enhanced Configuration File
```json
{
  "safety": {
    "failsafe_enabled": true,
    "pause_duration": 0.5,
    "confirmation_required": true
  },
  "whatsapp": {
    "wait_time": 20,
    "close_time": 5,
    "client": "web",
    "retry_attempts": 3,
    "headless_mode": false,
    "delivery_confirmation": true
  },
  "selenium": {
    "window_size": [1920, 1080],
    "timeout": 30,
    "headless_mode": false,
    "user_data_dir": null,
    "disable_images": false,
    "disable_javascript": false
  },
  "screen": {
    "screenshot_dir": "screenshots",
    "monitor_interval": 60,
    "image_quality": 90,
    "save_fullscreen": true
  },
  "notifications": {
    "enabled": true,
    "on_completion": true,
    "on_error": true,
    "slack_channel": "#alerts",
    "email_recipients": ["admin@example.com"]
  },
  "performance": {
    "monitoring_enabled": true,
    "auto_cleanup": true,
    "max_memory_mb": 1000,
    "cleanup_interval": 3600
  },
  "security": {
    "encryption_enabled": true,
    "secure_credentials": true,
    "session_timeout": 3600
  }
}
```

## 🔐 Security Features

### Credential Encryption
```python
# Enable encryption
agent.enable_encryption()

# Set encrypted credentials
agent.set_credentials({
    "whatsapp_session": "/secure/session/path",
    "smtp_password": "encrypted_password",
    "api_keys": "encrypted_api_keys"
})

# Retrieve securely
password = agent.get_credential("smtp_password")
```

### Secure Production Deployment
```python
# Production-ready configuration
agent = EnhancedAutomationAgent(
    headless_mode=True,
    safety_level=SafetyLevel.HIGH,
    timeout=60,
    retry_attempts=5
)

# Enable all security features
agent.enable_encryption()
agent.start_performance_monitoring()
agent.set_config("security.encryption_enabled", True)
```

## 🧪 Testing & Validation

### Automated Testing
```python
def test_whatsapp_messaging():
    """Test WhatsApp functionality."""
    agent = create_enhanced_agent(headless=True)
    
    success = agent.send_whatsapp_message_selenium(
        phone_number="256701234567",
        message="Test message",
        wait_for_delivery=True
    )
    
    assert success, "WhatsApp messaging failed"
    assert agent.message_sent_successfully(), "Message not sent"
    
    return True

def test_scheduling():
    """Test task scheduling."""
    agent = create_enhanced_agent()
    
    task = AutomationTask(
        name="Test Task",
        function=lambda: "test",
        schedule_type="daily",
        schedule_time="12:00"
    )
    
    task_id = agent.add_task(task)
    assert task_id, "Scheduling failed"
    assert agent.task_scheduled(), "Task not scheduled"
    
    return True

# Run tests
results = []
tests = [
    ("Messaging", test_whatsapp_messaging),
    ("Scheduling", test_scheduling)
]

for name, test_func in tests:
    try:
        result = test_func()
        results.append((name, "PASSED" if result else "FAILED"))
    except Exception as e:
        results.append((name, "FAILED"))
        print(f"Test {name} failed: {e}")
```

### Performance Validation
```python
# Performance testing
agent.start_performance_monitoring()

# Run test operations
for i in range(100):
    agent.move_mouse(i % 100, i % 100)
    agent.click()

agent.stop_performance_monitoring()

# Get results
stats = agent.get_performance_stats()
print(f"Average operation time: {stats['duration_seconds']/100:.4f}s")
print(f"Memory usage: {stats['memory_mb']:.2f}MB")
```

## 📊 Performance Optimization

### Multi-threading Support
```python
import threading

def parallel_operations():
    """Run multiple operations in parallel."""
    
    def send_messages_batch(batch):
        for contact in batch:
            agent.send_whatsapp_message_selenium(
                contact["phone"],
                contact["message"]
            )
    
    # Split contacts into batches
    contacts = [...]  # Your contact list
    batch_size = 5
    batches = [contacts[i:i+batch_size] for i in range(0, len(contacts), batch_size)]
    
    # Run batches in parallel
    threads = []
    for batch in batches:
        thread = threading.Thread(target=send_messages_batch, args=(batch,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
```

### Resource Optimization
```python
# Automatic cleanup
agent.set_config("performance.auto_cleanup", True)
agent.set_config("performance.max_memory_mb", 500)

# Memory monitoring
stats = agent.get_performance_stats()
if stats["memory_mb"] > 800:
    print("⚠️ High memory usage - consider cleanup")

# Headless mode for bulk operations
agent = EnhancedAutomationAgent(headless_mode=True)
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### ChromeDriver Compatibility
```python
# Automatic version matching
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

#### WhatsApp Loading Failures
```python
# Increase wait times
agent.set_config("whatsapp.wait_time", 45)
agent.set_config("selenium.timeout", 60)

# Use headless mode to prevent interference
agent = EnhancedAutomationAgent(headless_mode=True)
```

#### Element Detection Problems
```python
# Lower confidence threshold
agent.click_image("button.png", confidence=0.7)

# Wait explicitly for elements
element = agent.wait_for_element("#main", timeout=60, clickable=True)
if element:
    element.click()
```

#### Memory Issues
```python
# Enable automatic cleanup
agent.set_config("performance.auto_cleanup", True)

# Monitor and clean up
import gc
gc.collect()

# Close browser sessions
agent.cleanup()
```

### Debug Mode
```python
# Enable detailed logging
import logging
agent = EnhancedAutomationAgent(log_level=logging.DEBUG)

# Take diagnostic screenshots
agent.take_screenshot("debug_screenshot.png")

# Check browser state
print(f"Current URL: {agent.driver.current_url}")
print(f"Page title: {agent.driver.title}")
```

## 📈 Monitoring & Analytics

### Real-time Monitoring
```python
# Enable continuous monitoring
agent.start_performance_monitoring()

# Monitor specific operations
def monitored_whatsapp(phone, message):
    agent.start_performance_monitoring()
    try:
        result = agent.send_whatsapp_message_selenium(phone, message)
        return result
    finally:
        agent.stop_performance_monitoring()

# Periodic status checks
def periodic_status_check():
    stats = agent.get_performance_stats()
    
    if stats["memory_mb"] > 1000:
        agent.send_slack_notification(
            "#monitoring", 
            f"⚠️ High memory usage: {stats['memory_mb']:.2f}MB"
        )
```

### Performance Reports
```python
# Generate performance report
def generate_report():
    stats = agent.get_performance_stats()
    
    report = f"""
Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Operations: {stats['operations_count']}
Duration: {stats['duration_seconds']:.2f}s
Memory Peak: {stats['memory_mb']:.2f}MB
CPU Average: {stats['cpu_percent']:.1f}%
Errors: {stats['errors_count']}
    """.strip()
    
    agent.send_email("admin@example.com", "Performance Report", report)
    return report
```

## 🆘 Support

### Getting Help
1. Check the troubleshooting section above
2. Review examples in `enhanced_examples.py`
3. Run the test suite: `python test_automation_agent.py`
4. Check log files in `automation_logs/` directory

### Common Commands
```bash
# Test installation
python -c "from enhanced_automation_agent import *; print('Enhanced Agent Ready!')"

# Run examples
python enhanced_examples.py

# Run tests
python test_automation_agent.py

# Launch dashboard
python dashboard.py

# Generate test report
python test_automation_agent.py --report
```

## 🎯 Use Cases Summary

✅ **WhatsApp Daily Messages at 9 AM** - Enhanced with delivery confirmation and retry logic
✅ **Chrome Automation with Form Filling** - Selenium integration for robust web automation
✅ **Copy/Paste Between Applications** - Multi-application workflow automation
✅ **Hourly Screenshots with Timestamps** - Performance monitoring and storage optimization
✅ **Excel Macro Execution and Saving** - Script execution with error handling
✅ **Email Monitoring and Auto-Reply** - Multi-channel notification system
✅ **File Downloads at Scheduled Times** - Bulk operations with rate limiting

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "enhanced_automation_agent.py"]
```

### Service Configuration
```bash
# Create systemd service
sudo nano /etc/systemd/system/automation-agent.service

[Unit]
Description=AI Automation Agent
After=network.target

[Service]
Type=simple
User=automation
WorkingDirectory=/opt/automation-agent
ExecStart=/opt/automation-agent/venv/bin/python enhanced_automation_agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🎉 Enhanced Features Summary

✅ **Selenium WebDriver Integration** - Professional browser automation  
✅ **Automatic ChromeDriver Management** - No manual setup required  
✅ **Bulk WhatsApp Operations** - Mass messaging with intelligent rate limiting  
✅ **Performance Monitoring** - Real-time system metrics and optimization  
✅ **Production Deployment** - Enterprise-grade configuration and security  
✅ **Advanced Error Handling** - Comprehensive retry logic and recovery  
✅ **Multi-Channel Notifications** - Slack, Email, and system alerts  
✅ **Credential Encryption** - Secure handling of sensitive data  
✅ **Website Performance Testing** - Load time and availability monitoring  
✅ **Script Execution** - Integration with external automation scripts  
✅ **Multi-Session Support** - Multiple browser profiles for different contexts  
✅ **Resource Optimization** - Memory management and cleanup automation  
✅ **Testing Framework Integration** - Automated testing with assertions  
✅ **Comprehensive Documentation** - Complete API reference and examples  

**Ready for Production Deployment! 🚀**# sanaa-gui-agent
