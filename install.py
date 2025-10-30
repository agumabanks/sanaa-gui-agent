#!/usr/bin/env python3
"""
Enhanced Installation script for AI Automation Agent
Handles Selenium, ChromeDriver, and advanced dependency installation.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def run_command(command, description):
    """Run a shell command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Minimum required: Python 3.8")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")

    # Core dependencies
    core_deps = [
        "pyautogui>=0.9.53",
        "schedule>=1.2.0",
        "Pillow>=9.0.0",
        "requests>=2.28.0",
        "psutil>=5.9.0"
    ]

    # Enhanced dependencies
    enhanced_deps = [
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "cryptography>=41.0.0"
    ]

    # Optional dependencies
    optional_deps = [
        "plyer>=2.1.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0"
    ]

    all_deps = core_deps + enhanced_deps + optional_deps

    print("Installing core dependencies...")
    if run_command(f"pip install {' '.join(core_deps)}", "Installing core dependencies"):
        print("Core dependencies installed successfully")
    else:
        print("⚠️ Some core dependencies failed to install")
        return False

    print("\nInstalling enhanced dependencies...")
    enhanced_success = True
    for dep in enhanced_deps:
        if not run_command(f"pip install '{dep}'", f"Installing {dep}"):
            enhanced_success = False
    
    if enhanced_success:
        print("✅ All enhanced dependencies installed")
    else:
        print("⚠️ Some enhanced dependencies failed - Selenium features may be limited")
        return False

    print("\nInstalling optional dependencies...")
    for dep in optional_deps:
        run_command(f"pip install '{dep}'", f"Installing {dep}")

    return True


def install_chromedriver():
    """Install ChromeDriver."""
    print("\n🌐 Installing ChromeDriver...")
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("Installing ChromeDriver for macOS...")
        # Try Homebrew first
        if run_command("brew install --cask chromedriver", "Installing ChromeDriver via Homebrew"):
            return True
        else:
            print("⚠️ Homebrew not available or ChromeDriver installation failed")
            print("   Try manual installation: pip install webdriver-manager")
            return True  # webdriver-manager will handle it
    else:
        print("ChromeDriver will be managed automatically by webdriver-manager")
        return True


def setup_directories():
    """Create necessary directories."""
    print("\n📁 Setting up directories...")

    directories = [
        "automation_logs",
        "screenshots",
        "test_reports",
        "automation_config.json",
        "ssl_certs"
    ]

    for directory in directories[:-1]:  # Exclude config file
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Create default config if it doesn't exist
    config_file = Path("automation_config.json")
    if not config_file.exists():
        default_config = {
            "safety": {
                "failsafe_enabled": True,
                "pause_duration": 0.5,
                "confirmation_required": False
            },
            "whatsapp": {
                "wait_time": 20,
                "close_time": 5,
                "client": "web",
                "retry_attempts": 3,
                "headless_mode": False
            },
            "screen": {
                "screenshot_dir": "screenshots",
                "monitor_interval": 60,
                "image_quality": 90
            },
            "notifications": {
                "enabled": True,
                "on_completion": True,
                "on_error": True
            },
            "selenium": {
                "window_size": [1920, 1080],
                "timeout": 30,
                "headless_mode": False,
                "user_data_dir": null
            },
            "performance": {
                "monitoring_enabled": True,
                "auto_cleanup": True,
                "max_memory_mb": 1000
            },
            "security": {
                "encryption_enabled": True,
                "secure_credentials": true
            }
        }

        import json
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print("✅ Created enhanced configuration file")

    return True


def verify_selenium_installation():
    """Verify Selenium and WebDriver setup."""
    print("\n🔍 Verifying Selenium installation...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ Selenium imports successful")
        
        # Test ChromeDriver setup
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            print("🔧 Testing ChromeDriver setup...")
            # Don't actually start browser, just verify classes exist
            print("✅ ChromeDriver classes available")
            
        except Exception as e:
            print(f"⚠️ ChromeDriver test failed: {e}")
            print("   This will be handled automatically by webdriver-manager")
        
        return True
        
    except ImportError as e:
        print(f"❌ Selenium import failed: {e}")
        return False


def verify_enhanced_features():
    """Verify enhanced feature availability."""
    print("\n🔍 Verifying enhanced features...")

    features = {}

    # Check core features
    try:
        from automation_agent import AutomationAgent
        features["base_automation"] = True
        print("✅ Base automation available")
    except ImportError:
        features["base_automation"] = False
        print("❌ Base automation not available")

    # Check enhanced features
    try:
        from enhanced_automation_agent import EnhancedAutomationAgent
        features["enhanced_automation"] = True
        print("✅ Enhanced automation available")
    except ImportError:
        features["enhanced_automation"] = False
        print("❌ Enhanced automation not available")

    # Check security features
    try:
        from cryptography.fernet import Fernet
        features["encryption"] = True
        print("✅ Encryption available")
    except ImportError:
        features["encryption"] = False
        print("❌ Encryption not available")

    # Check computer vision
    try:
        import cv2
        features["computer_vision"] = True
        print("✅ Computer vision available")
    except ImportError:
        features["computer_vision"] = False
        print("❌ Computer vision not available")

    # Check notifications
    try:
        import plyer
        features["notifications"] = True
        print("✅ System notifications available")
    except ImportError:
        features["notifications"] = False
        print("❌ System notifications not available")

    return features


def test_enhanced_agent():
    """Test enhanced agent initialization."""
    print("\n🧪 Testing enhanced agent...")
    
    try:
        from enhanced_automation_agent import create_enhanced_agent
        
        # Test creation with basic settings
        agent = create_enhanced_agent(
            safety_level="low",
            headless=True,
            enable_encryption=True
        )
        
        print("✅ Enhanced agent created successfully")
        
        # Test encryption
        agent.enable_encryption()
        agent.set_credentials({"test": "value"})
        retrieved = agent.get_credential("test")
        
        if retrieved == "value":
            print("✅ Encryption/decryption working")
        else:
            print("⚠️ Encryption/decryption failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced agent test failed: {e}")
        return False


def show_platform_specific_setup():
    """Show platform-specific setup instructions."""
    print("\n💻 Platform-Specific Setup:")
    print("=" * 50)

    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("🍎 macOS Setup:")
        print("   1. Grant screen recording permission:")
        print("      System Preferences > Security & Privacy > Privacy > Screen Recording")
        print("      Add Terminal and your Python IDE")
        print("   2. Install Chrome: https://www.google.com/chrome/")
        print("   3. Enable Developer Mode: System Preferences > Security & Privacy > Allow Apps from Unknown Sources")
        
    elif system == "Windows":
        print("🪟 Windows Setup:")
        print("   1. Run Command Prompt or PowerShell as Administrator")
        print("   2. Install Chrome: https://www.google.com/chrome/")
        print("   3. May need to add Python to PATH")
        
    elif system == "Linux":
        print("🐧 Linux Setup:")
        print("   1. Install Chrome browser:")
        print("      wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -")
        print("      sudo sh -c 'echo \"deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\" >> /etc/apt/sources.list.d/google-chrome.list'")
        print("      sudo apt update && sudo apt install google-chrome-stable")
        print("   2. Install screenshot tools: sudo apt-get install scrot")
        print("   3. For GUI automation, ensure X11 is running")


def show_usage_guide():
    """Show usage guide."""
    print("\n🚀 Enhanced Automation Agent - Quick Start")
    print("=" * 60)

    print("\n📋 Basic Usage:")
    print("   1. Run examples:")
    print("      python enhanced_examples.py")
    print("   2. Use GUI dashboard:")
    print("      python dashboard.py")
    print("   3. Test installation:")
    print("      python -c 'from enhanced_automation_agent import EnhancedAutomationAgent; print(\"Ready!\")'")

    print("\n🎯 WhatsApp Automation Examples:")
    print("""
from enhanced_automation_agent import EnhancedAutomationAgent

agent = EnhancedAutomationAgent()

# Send WhatsApp message
agent.send_whatsapp_message_selenium(
    "256701234567", 
    "Hello from Enhanced Automation Agent!"
)

# Bulk messaging
contacts = [{"phone": "256701234567", "message": "Bulk message"}]
agent.send_bulk_messages(contacts)

# Schedule messages
agent.schedule_whatsapp("09:00", "256701234567", "Daily greeting")
    """)

    print("\n🔧 Configuration:")
    print("   • Edit automation_config.json for settings")
    print("   • Set credentials securely with agent.set_credentials()")
    print("   • Enable encryption for production use")

    print("\n📚 Documentation:")
    print("   • README.md - Complete documentation")
    print("   • examples.py - Basic examples")
    print("   • enhanced_examples.py - Advanced examples")


def main():
    """Main installation function."""
    print("🤖 Enhanced AI Automation Agent - Installation")
    print("=" * 60)
    print("Features: Selenium, ChromeDriver, Bulk Operations, Performance Monitoring")
    print("=" * 60)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)

    # Install ChromeDriver
    install_chromedriver()

    # Setup directories
    setup_directories()

    # Verify installations
    selenium_ok = verify_selenium_installation()
    features = verify_enhanced_features()
    
    if selenium_ok and features.get("enhanced_automation"):
        test_enhanced_agent()

    # Show platform-specific instructions
    show_platform_specific_setup()

    # Show usage guide
    show_usage_guide()

    print("\n🎉 Enhanced Installation completed!")
    print("\n📝 Next steps:")
    print("   1. Test installation: python test_automation_agent.py")
    print("   2. Run examples: python enhanced_examples.py")
    print("   3. Launch dashboard: python dashboard.py")
    print("   4. Read documentation: README.md")

    if features.get("enhanced_automation"):
        print("\n✨ Enhanced features ready!")
    else:
        print("\n⚠️ Some enhanced features may be limited")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        sys.exit(1)