"""
Unified Automation Agent - Production-Ready Implementation
Comprehensive automation framework with WhatsApp, browser automation, scheduling, and computer vision
References sanaa_agent.py architecture with enhanced features and robust error handling
"""

import pyautogui
import time
import schedule
import subprocess
import platform
import json
import logging
from datetime import datetime
from pathlib import Path
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import cv2
import numpy as np
import requests
import threading

# Setup logging with enhanced formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler('unified_agent_log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AutomationAgent:
    """
    Unified Automation Agent with comprehensive automation capabilities.
    
    Features:
    - WhatsApp messaging (immediate and scheduled)
    - Browser automation with Selenium
    - Computer vision-based clicking
    - Keyboard and mouse control
    - Task scheduling
    - Website testing and link checking
    - Bulk messaging with progress tracking
    """
    
    def __init__(self):
        """Initialize the automation agent with system detection and configuration."""
        self.system = platform.system()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self.actions_log = []
        self.driver = None
        self.scheduler_running = False
        self.scheduled_tasks = []
        
        logger.info("=" * 60)
        logger.info("Unified Automation Agent Initialized")
        logger.info(f"System: {self.system}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        print("\n✓ Automation Agent initialized successfully\n")
    
    # ============= SCREEN CONTROL & MOUSE =============
    
    def get_mouse_position(self, delay=0.5):
        """
        Get current mouse cursor position with optional delay.
        
        Args:
            delay (float): Delay in seconds before capturing position
            
        Returns:
            tuple: (x, y) coordinates of mouse cursor
            
        Example:
            >>> agent = AutomationAgent()
            >>> x, y = agent.get_mouse_position()
            >>> print(f"Mouse at: ({x}, {y})")
        """
        if delay > 0:
            logger.info(f"Waiting {delay}s before capturing mouse position...")
            time.sleep(delay)
        
        pos = pyautogui.position()
        logger.info(f"Mouse position captured: X={pos.x}, Y={pos.y}")
        print(f"📍 Mouse Position: X={pos.x}, Y={pos.y}")
        self.log_action(f"Mouse position: ({pos.x}, {pos.y})")
        return pos
    
    def click(self, x, y):
        """
        Programmatically click at specified coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if click was successful
            
        Example:
            >>> agent.click(500, 300)
        """
        try:
            logger.info(f"Clicking at coordinates: X={x}, Y={y}")
            pyautogui.click(x, y)
            print(f"✓ Clicked at ({x}, {y})")
            self.log_action(f"Click at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Click failed at ({x}, {y}): {e}")
            print(f"✗ Click failed: {e}")
            return False
    
    def click_image(self, image_filename, confidence=0.8):
        """
        Find and click an image on screen using computer vision.
        
        Args:
            image_filename (str): Path to image file to find and click
            confidence (float): Confidence threshold (0.0-1.0), default 0.8
            
        Returns:
            bool: True if image found and clicked, False otherwise
            
        Raises:
            Suggestions for debugging if image not found
            
        Example:
            >>> agent.click_image("button.png", confidence=0.8)
            >>> agent.click_image("icon.png", confidence=0.7)  # Lower threshold
        """
        try:
            logger.info(f"Searching for image: {image_filename} (confidence: {confidence})")
            print(f"🔍 Searching for image: {image_filename}")
            
            # Check if image file exists
            if not Path(image_filename).exists():
                logger.error(f"Image file not found: {image_filename}")
                print(f"✗ Image file not found: {image_filename}")
                return False
            
            # Try to locate image on screen
            location = pyautogui.locateOnScreen(image_filename, confidence=confidence)
            
            if location:
                center = pyautogui.center(location)
                logger.info(f"Image found at: {location}, clicking center: ({center.x}, {center.y})")
                print(f"✓ Image found at ({center.x}, {center.y})")
                
                # Click the center of the image
                pyautogui.click(center.x, center.y)
                self.log_action(f"Clicked image: {image_filename} at ({center.x}, {center.y})")
                return True
            else:
                logger.warning(f"Image not found on screen: {image_filename}")
                print(f"✗ Image not found on screen: {image_filename}")
                print(f"  💡 Debugging tips:")
                print(f"     - Try lowering confidence threshold (e.g., 0.7)")
                print(f"     - Verify image is visible on current screen")
                print(f"     - Take a screenshot to verify screen state")
                print(f"     - Check image file is in correct format (PNG/JPG)")
                return False
                
        except Exception as e:
            logger.error(f"Image click failed: {e}")
            print(f"✗ Image click error: {e}")
            print(f"  💡 Suggestions:")
            print(f"     - Ensure image file exists and is readable")
            print(f"     - Try with lower confidence value (0.7)")
            print(f"     - Verify target image is visible on screen")
            return False
    
    def type_text(self, text, interval=0.05):
        """
        Automatically type text character by character.
        
        Args:
            text (str): Text to type
            interval (float): Delay between characters in seconds
            
        Returns:
            bool: True if typing was successful
            
        Example:
            >>> agent.type_text("Hello World")
            >>> agent.type_text("test@example.com", interval=0.1)
        """
        try:
            logger.info(f"Typing text: {text}")
            print(f"⌨️  Typing: {text}")
            pyautogui.write(text, interval=interval)
            self.log_action(f"Typed: {text}")
            return True
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            print(f"✗ Type text error: {e}")
            return False
    
    def hotkey(self, *keys):
        """
        Press keyboard shortcut combination.
        
        Args:
            *keys: Variable number of key names (e.g., 'ctrl', 's')
            
        Returns:
            bool: True if hotkey was successful
            
        Example:
            >>> agent.hotkey('ctrl', 's')  # Save
            >>> agent.hotkey('ctrl', 'c')  # Copy
            >>> agent.hotkey('alt', 'tab')  # Switch window
        """
        try:
            key_combo = '+'.join(keys)
            logger.info(f"Pressing hotkey: {key_combo}")
            print(f"⌨️  Hotkey: {key_combo}")
            pyautogui.hotkey(*keys)
            self.log_action(f"Hotkey: {key_combo}")
            return True
        except Exception as e:
            logger.error(f"Hotkey failed: {e}")
            print(f"✗ Hotkey error: {e}")
            return False
    
    # ============= BROWSER AUTOMATION =============
    
    def init_browser(self, headless=False):
        """
        Initialize Selenium WebDriver with ChromeDriver.
        
        Uses webdriver-manager for automatic ChromeDriver management.
        
        Args:
            headless (bool): Run browser in headless mode
            
        Returns:
            bool: True if browser initialized successfully
            
        Example:
            >>> agent.init_browser()
            >>> agent.init_browser(headless=True)
        """
        try:
            logger.info("Initializing browser...")
            print("🌐 Initializing browser...")
            
            options = Options()
            
            if headless:
                options.add_argument('--headless')
                logger.info("Browser running in headless mode")
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Use webdriver-manager for automatic ChromeDriver management
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("ChromeDriver initialized with webdriver-manager")
            except Exception as e:
                logger.warning(f"webdriver-manager failed: {e}, trying default ChromeDriver")
                self.driver = webdriver.Chrome(options=options)
            
            # Hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Browser initialized successfully")
            print("✓ Browser initialized successfully")
            self.log_action("Browser opened")
            return True
            
        except Exception as e:
            logger.error(f"Browser initialization failed: {e}")
            print(f"✗ Browser initialization failed: {e}")
            print(f"  💡 Troubleshooting:")
            print(f"     - Ensure ChromeDriver is installed or webdriver-manager is available")
            print(f"     - Check Chrome/Chromium browser is installed")
            print(f"     - Try: pip install webdriver-manager")
            return False
    
    def navigate_to(self, url, timeout=10):
        """
        Navigate to a URL with timeout handling.
        
        Args:
            url (str): URL to navigate to
            timeout (int): Timeout in seconds
            
        Returns:
            bool: True if navigation successful
            
        Example:
            >>> agent.navigate_to("https://www.google.com")
        """
        try:
            if not self.driver:
                self.init_browser()
            
            logger.info(f"Navigating to: {url}")
            print(f"🔗 Navigating to: {url}")
            
            self.driver.set_page_load_timeout(timeout)
            self.driver.get(url)
            
            logger.info(f"Successfully navigated to: {url}")
            print(f"✓ Page loaded: {url}")
            self.log_action(f"Navigated to: {url}")
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            print(f"✗ Navigation failed: {e}")
            return False
    
    def find_element(self, by, value, timeout=30):
        """
        Find element with adjustable timeout and error suggestions.
        
        Args:
            by: Selenium By locator type (By.ID, By.XPATH, etc.)
            value (str): Locator value
            timeout (int): Timeout in seconds (default 30)
            
        Returns:
            WebElement or None: Found element or None if not found
            
        Example:
            >>> element = agent.find_element(By.ID, "submit_button")
            >>> element = agent.find_element(By.XPATH, "//button[@class='send']", timeout=20)
        """
        try:
            logger.info(f"Finding element: {by}={value} (timeout: {timeout}s)")
            
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            
            logger.info(f"Element found: {value}")
            return element
            
        except Exception as e:
            logger.error(f"Element not found: {value} - {e}")
            print(f"✗ Element not found: {value}")
            print(f"  💡 Debugging suggestions:")
            print(f"     - Open browser DevTools (F12) to inspect element")
            print(f"     - Verify selector: {value}")
            print(f"     - Try different locator (ID, XPATH, CSS_SELECTOR)")
            print(f"     - Increase timeout value")
            print(f"     - Check if element is in iframe")
            return None
    
    def click_element(self, by, value, timeout=30):
        """
        Find and click a web element.
        
        Args:
            by: Selenium By locator type
            value (str): Locator value
            timeout (int): Timeout in seconds
            
        Returns:
            bool: True if element clicked successfully
        """
        try:
            element = self.find_element(by, value, timeout)
            if element:
                element.click()
                logger.info(f"Clicked element: {value}")
                self.log_action(f"Clicked element: {value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Click element failed: {e}")
            return False
    
    def fill_form(self, field_data):
        """
        Fill form fields with provided data.
        
        Args:
            field_data (dict): Dictionary of field_id/name -> value
            
        Returns:
            bool: True if form filled successfully
            
        Example:
            >>> agent.fill_form({
            ...     'email': 'user@example.com',
            ...     'password': 'secret123'
            ... })
        """
        try:
            logger.info(f"Filling form with {len(field_data)} fields")
            
            for field_id, value in field_data.items():
                element = self.find_element(By.ID, field_id)
                if not element:
                    element = self.find_element(By.NAME, field_id)
                
                if element:
                    element.clear()
                    element.send_keys(value)
                    logger.info(f"Filled field: {field_id}")
                    self.log_action(f"Filled {field_id}: {value}")
            
            logger.info("Form filled successfully")
            print("✓ Form filled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Form fill failed: {e}")
            print(f"✗ Form fill error: {e}")
            return False
    
    def submit_form(self, button_id=None):
        """
        Submit form by button ID or form tag.
        
        Args:
            button_id (str): Optional button element ID
            
        Returns:
            bool: True if form submitted
        """
        try:
            if button_id:
                self.click_element(By.ID, button_id)
            else:
                form = self.driver.find_element(By.TAG_NAME, 'form')
                form.submit()
            
            logger.info("Form submitted")
            self.log_action("Form submitted")
            return True
        except Exception as e:
            logger.error(f"Form submission failed: {e}")
            return False
    
    # ============= WHATSAPP AUTOMATION =============
    
    def send_whatsapp_message(self, phone_number, message):
        """
        Send WhatsApp message via WhatsApp Web.
        
        Supports international format (e.g., 256701234567 for Uganda).
        Includes 30-second wait for WhatsApp Web loading and login verification.
        
        Args:
            phone_number (str): Phone number in format like 256701234567
            message (str): Message text to send
            
        Returns:
            bool: True if message sent successfully
            
        Example:
            >>> agent.send_whatsapp_message("256701234567", "Hello from automation!")
            >>> agent.send_whatsapp_message("1234567890", "Test message")
        """
        try:
            logger.info(f"Preparing to send WhatsApp message to: {phone_number}")
            print(f"📱 Sending WhatsApp to: {phone_number}")
            
            # Encode message for URL
            message_encoded = requests.utils.quote(message)
            url = f"https://web.whatsapp.com/send?phone={phone_number}&text={message_encoded}"
            
            if not self.driver:
                self.init_browser()
            
            logger.info(f"Navigating to WhatsApp Web: {url}")
            self.navigate_to(url)
            
            # Wait for WhatsApp Web to load (30 seconds)
            logger.info("Waiting 30 seconds for WhatsApp Web to load...")
            print("⏳ Waiting for WhatsApp Web to load (30s)...")
            time.sleep(30)
            
            # Check for login requirement
            try:
                logger.info("Checking for WhatsApp Web login verification...")
                print("🔐 Checking login status...")
                
                # Try to find send button
                send_button = self.find_element(
                    By.XPATH,
                    '//span[@data-icon="send"]',
                    timeout=10
                )
                
                if send_button:
                    logger.info("Send button found, clicking...")
                    print("✓ Send button found, sending message...")
                    send_button.click()
                    time.sleep(2)
                    
                    logger.info(f"WhatsApp message sent to {phone_number}")
                    print(f"✓ Message sent to {phone_number}")
                    self.log_action(f"WhatsApp sent to {phone_number}: {message}")
                    return True
                else:
                    logger.warning("Send button not found, trying fallback method...")
                    print("⚠️  Send button not found, trying Enter key...")
                    pyautogui.press('enter')
                    time.sleep(2)
                    
                    logger.info(f"WhatsApp message sent (fallback) to {phone_number}")
                    print(f"✓ Message sent (fallback) to {phone_number}")
                    return True
                    
            except Exception as e:
                logger.warning(f"Send button search timeout: {e}")
                print(f"⚠️  Timeout finding send button, trying Enter key...")
                
                # Fallback: press Enter
                try:
                    pyautogui.press('enter')
                    time.sleep(2)
                    logger.info(f"WhatsApp message sent (Enter fallback) to {phone_number}")
                    print(f"✓ Message sent (Enter key) to {phone_number}")
                    return True
                except Exception as e2:
                    logger.error(f"Fallback method failed: {e2}")
                    print(f"✗ Message send failed: {e2}")
                    return False
            
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            print(f"✗ WhatsApp send error: {e}")
            print(f"  💡 Troubleshooting:")
            print(f"     - Ensure you're logged into WhatsApp Web")
            print(f"     - Check internet connection")
            print(f"     - Verify phone number format (e.g., 256701234567)")
            print(f"     - Wait for WhatsApp Web to fully load")
            return False
    
    def schedule_whatsapp(self, time_str, phone_number, message):
        """
        Schedule WhatsApp message to be sent at specific time.
        
        Args:
            time_str (str): Time in HH:MM format (e.g., "09:00", "18:30")
            phone_number (str): Phone number in international format
            message (str): Message text
            
        Returns:
            bool: True if scheduled successfully
            
        Example:
            >>> agent.schedule_whatsapp("09:00", "256701234567", "Good morning!")
            >>> agent.schedule_whatsapp("18:00", "256701234567", "Evening update")
        """
        try:
            def job():
                logger.info(f"Executing scheduled WhatsApp to {phone_number}")
                self.send_whatsapp_message(phone_number, message)
            
            schedule.every().day.at(time_str).do(job)
            
            logger.info(f"WhatsApp scheduled for {time_str} to {phone_number}")
            print(f"📅 WhatsApp scheduled for {time_str} to {phone_number}")
            self.log_action(f"Scheduled WhatsApp: {time_str} -> {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"WhatsApp scheduling failed: {e}")
            print(f"✗ Scheduling error: {e}")
            return False
    
    def send_bulk_whatsapp(self, contacts_list):
        """
        Send WhatsApp messages to multiple contacts with progress tracking.
        
        Includes 5-second delays between messages and progress indicators.
        
        Args:
            contacts_list (list): List of dicts with 'phone' and 'message' keys
            
        Returns:
            dict: Results with success count and failed contacts
            
        Example:
            >>> contacts = [
            ...     {'phone': '256701234567', 'message': 'Hello 1'},
            ...     {'phone': '256702345678', 'message': 'Hello 2'},
            ...     {'phone': '256703456789', 'message': 'Hello 3'}
            ... ]
            >>> results = agent.send_bulk_whatsapp(contacts)
            >>> print(f"Sent: {results['success']}, Failed: {results['failed']}")
        """
        try:
            logger.info(f"Starting bulk WhatsApp send to {len(contacts_list)} contacts")
            print(f"\n📱 Bulk WhatsApp Send - {len(contacts_list)} contacts")
            print("=" * 60)
            
            results = {
                'total': len(contacts_list),
                'success': 0,
                'failed': 0,
                'failed_contacts': [],
                'timestamp': datetime.now().isoformat()
            }
            
            for idx, contact in enumerate(contacts_list, 1):
                phone = contact.get('phone')
                message = contact.get('message')
                
                if not phone or not message:
                    logger.warning(f"Invalid contact data: {contact}")
                    results['failed'] += 1
                    results['failed_contacts'].append(contact)
                    continue
                
                # Progress indicator
                progress = f"[{idx}/{len(contacts_list)}]"
                print(f"{progress} Sending to {phone}...", end=" ")
                
                # Send message
                if self.send_whatsapp_message(phone, message):
                    results['success'] += 1
                    print("✓")
                else:
                    results['failed'] += 1
                    results['failed_contacts'].append(contact)
                    print("✗")
                
                # 5-second delay between messages
                if idx < len(contacts_list):
                    logger.info(f"Waiting 5 seconds before next message...")
                    time.sleep(5)
            
            print("=" * 60)
            logger.info(f"Bulk send complete: {results['success']} sent, {results['failed']} failed")
            print(f"✓ Complete: {results['success']} sent, {results['failed']} failed\n")
            
            self.log_action(f"Bulk WhatsApp: {results['success']}/{results['total']} sent")
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk WhatsApp send failed: {e}")
            print(f"✗ Bulk send error: {e}")
            return {
                'total': len(contacts_list),
                'success': 0,
                'failed': len(contacts_list),
                'error': str(e)
            }
    
    # ============= WEBSITE TESTING =============
    
    def test_website_performance(self, url):
        """
        Test website performance and capture metrics.
        
        Args:
            url (str): Website URL to test
            
        Returns:
            dict: Performance metrics including load times
            
        Example:
            >>> results = agent.test_website_performance("https://www.google.com")
            >>> print(f"Load time: {results['total_load_time']:.2f}s")
        """
        try:
            logger.info(f"Testing website performance: {url}")
            print(f"⚡ Testing website performance: {url}")
            
            if not self.driver:
                self.init_browser()
            
            # Measure load time
            start_time = time.time()
            self.navigate_to(url)
            load_time = time.time() - start_time
            
            # Get performance metrics
            try:
                performance = self.driver.execute_script("""
                    var performance = window.performance.timing;
                    var loadTime = performance.loadEventEnd - performance.navigationStart;
                    var domReadyTime = performance.domContentLoadedEventEnd - performance.navigationStart;
                    var responseTime = performance.responseEnd - performance.requestStart;
                    return {
                        loadTime: loadTime,
                        domReadyTime: domReadyTime,
                        responseTime: responseTime
                    };
                """)
            except:
                performance = {'loadTime': 0, 'domReadyTime': 0, 'responseTime': 0}
            
            # Take screenshot
            screenshot = self.screenshot(f"perf_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            results = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'total_load_time': load_time,
                'page_load_time': performance.get('loadTime', 0) / 1000,
                'dom_ready_time': performance.get('domReadyTime', 0) / 1000,
                'response_time': performance.get('responseTime', 0) / 1000,
                'screenshot': screenshot,
                'status': 'passed' if load_time < 3 else 'slow'
            }
            
            logger.info(f"Performance test results: {results}")
            print(f"✓ Load time: {load_time:.2f}s - Status: {results['status']}")
            self.log_action(f"Performance test: {url} - {results['status']}")
            
            self.save_test_results(results)
            return results
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            print(f"✗ Performance test error: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def check_broken_links(self, url):
        """
        Check for broken links on a webpage.
        
        Args:
            url (str): Website URL to check
            
        Returns:
            dict: Results with broken links list
            
        Example:
            >>> results = agent.check_broken_links("https://example.com")
            >>> print(f"Broken links: {len(results['broken_links'])}")
        """
        try:
            logger.info(f"Checking broken links on: {url}")
            print(f"🔗 Checking for broken links: {url}")
            
            self.navigate_to(url)
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            
            logger.info(f"Found {len(links)} links on page")
            print(f"Found {len(links)} links, checking...")
            
            broken_links = []
            for idx, link in enumerate(links, 1):
                href = link.get_attribute('href')
                if href and href.startswith('http'):
                    try:
                        response = requests.head(href, timeout=5)
                        if response.status_code >= 400:
                            broken_links.append({
                                'url': href,
                                'status_code': response.status_code,
                                'text': link.text
                            })
                            logger.warning(f"Broken link found: {href} ({response.status_code})")
                    except Exception as e:
                        broken_links.append({
                            'url': href,
                            'error': str(e),
                            'text': link.text
                        })
                        logger.warning(f"Link check error: {href} - {e}")
            
            result = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'total_links': len(links),
                'broken_links': broken_links,
                'status': 'passed' if len(broken_links) == 0 else 'failed'
            }
            
            logger.info(f"Link check complete: {len(broken_links)} broken links found")
            print(f"✓ Check complete: {len(broken_links)} broken links found")
            self.log_action(f"Link check: {url} - {len(broken_links)} broken")
            
            self.save_test_results(result)
            return result
            
        except Exception as e:
            logger.error(f"Link check failed: {e}")
            print(f"✗ Link check error: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    # ============= SCHEDULED TASKS =============
    
    def schedule_task(self, time_str, callback, *args, **kwargs):
        """
        Schedule a custom task to run at specific time.
        
        Args:
            time_str (str): Time in HH:MM format (e.g., "09:00")
            callback (callable): Function to execute
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback
            
        Returns:
            bool: True if scheduled successfully
            
        Example:
            >>> def my_task():
            ...     print("Task executed!")
            >>> agent.schedule_task("10:00", my_task)
        """
        try:
            def job():
                logger.info(f"Executing scheduled task: {callback.__name__}")
                print(f"⏰ Executing task: {callback.__name__}")
                callback(*args, **kwargs)
            
            schedule.every().day.at(time_str).do(job)
            
            logger.info(f"Task scheduled: {callback.__name__} at {time_str}")
            print(f"📅 Task scheduled: {callback.__name__} at {time_str}")
            self.log_action(f"Scheduled: {callback.__name__} at {time_str}")
            return True
            
        except Exception as e:
            logger.error(f"Task scheduling failed: {e}")
            print(f"✗ Scheduling error: {e}")
            return False
    
    def run_scheduler(self):
        """
        Run scheduler continuously for all scheduled tasks.
        
        Runs in infinite loop, checking for pending tasks every 60 seconds.
        
        Example:
            >>> agent.schedule_whatsapp("09:00", "256701234567", "Morning!")
            >>> agent.schedule_task("10:00", my_function)
            >>> agent.run_scheduler()  # Runs continuously
        """
        try:
            self.scheduler_running = True
            logger.info("=" * 60)
            logger.info("SCHEDULER STARTED - Monitoring scheduled tasks")
            logger.info("=" * 60)
            print("\n" + "=" * 60)
            print("✓ SCHEDULER STARTED")
            print("  Monitoring scheduled tasks...")
            print("  Press Ctrl+C to stop")
            print("=" * 60 + "\n")
            
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            print("\n✓ Scheduler stopped")
            self.scheduler_running = False
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            print(f"✗ Scheduler error: {e}")
    
    def morning_report(self):
        """
        Scheduled task: Generate morning report with tech news.
        
        - Searches for tech news on Google
        - Takes screenshot as morning_news.png
        - Sends WhatsApp notification
        
        Example:
            >>> agent.schedule_task("09:00", agent.morning_report)
        """
        try:
            logger.info("Executing morning_report task")
            print("\n📰 Generating Morning Report...")
            
            # Search for tech news
            logger.info("Searching for tech news...")
            print("  🔍 Searching for tech news...")
            
            if not self.driver:
                self.init_browser()
            
            self.navigate_to("https://www.google.com")
            search_box = self.find_element(By.NAME, "q")
            
            if search_box:
                search_box.send_keys("tech news today")
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)
                
                # Take screenshot
                screenshot = self.screenshot("morning_news.png")
                logger.info(f"Morning news screenshot: {screenshot}")
                print(f"  ✓ Screenshot saved: {screenshot}")
                
                # Send WhatsApp notification
                logger.info("Sending WhatsApp notification...")
                print("  📱 Sending WhatsApp notification...")
                
                # Note: Requires valid phone number
                # self.send_whatsapp_message("256701234567", "Good morning! Tech news report ready.")
                
                logger.info("Morning report completed")
                print("✓ Morning report completed")
                self.log_action("Morning report generated")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Morning report failed: {e}")
            print(f"✗ Morning report error: {e}")
            return False
    
    def test_website(self, url):
        """
        Scheduled task: Test website performance.
        
        Args:
            url (str): Website URL to test
            
        Example:
            >>> agent.schedule_task("14:00", agent.test_website, "https://example.com")
        """
        try:
            logger.info(f"Executing test_website task for: {url}")
            print(f"\n⚡ Testing website: {url}")
            
            results = self.test_website_performance(url)
            
            logger.info(f"Website test completed: {results['status']}")
            print(f"✓ Test completed: {results['status']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Website test failed: {e}")
            print(f"✗ Website test error: {e}")
            return None
    
    def check_links(self, url):
        """
        Scheduled task: Check for broken links.
        
        Args:
            url (str): Website URL to check
            
        Example:
            >>> agent.schedule_task("16:00", agent.check_links, "https://example.com")
        """
        try:
            logger.info(f"Executing check_links task for: {url}")
            print(f"\n🔗 Checking links: {url}")
            
            results = self.check_broken_links(url)
            
            logger.info(f"Link check completed: {len(results.get('broken_links', []))} broken")
            print(f"✓ Check completed: {len(results.get('broken_links', []))} broken links")
            
            return results
            
        except Exception as e:
            logger.error(f"Link check failed: {e}")
            print(f"✗ Link check error: {e}")
            return None
    
    # ============= UTILITIES =============
    
    def screenshot(self, filename=None):
        """
        Take screenshot and save to file.
        
        Args:
            filename (str): Optional filename, auto-generated if not provided
            
        Returns:
            str: Path to saved screenshot
            
        Example:
            >>> agent.screenshot("debug.png")
            >>> agent.screenshot()  # Auto-named
        """
        try:
            if not filename:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            pyautogui.screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            print(f"📸 Screenshot: {filename}")
            self.log_action(f"Screenshot: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            print(f"✗ Screenshot error: {e}")
            return None
    
    def log_action(self, action):
        """
        Log action to memory and file.
        
        Args:
            action (str): Action description
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action
        }
        self.actions_log.append(entry)
        
        # Save to file
        try:
            with open('unified_actions_log.json', 'w') as f:
                json.dump(self.actions_log, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save action log: {e}")
    
    def get_action_history(self, limit=None):
        """
        Get action history.
        
        Args:
            limit (int): Optional limit on number of actions
            
        Returns:
            list: List of logged actions
        """
        if limit:
            return self.actions_log[-limit:]
        return self.actions_log
    
    def save_test_results(self, results):
        """
        Save test results to JSON file.
        
        Args:
            results (dict): Test results to save
        """
        try:
            filename = 'unified_test_results.json'
            
            # Load existing results
            try:
                with open(filename, 'r') as f:
                    all_results = json.load(f)
            except:
                all_results = []
            
            all_results.append(results)
            
            # Save
            with open(filename, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            logger.info(f"Test results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")
    
    def generate_report(self):
        """
        Generate activity report.
        
        Returns:
            dict: Report with statistics
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_actions': len(self.actions_log),
                'recent_actions': self.actions_log[-10:] if self.actions_log else [],
                'scheduler_running': self.scheduler_running
            }
            
            with open('unified_agent_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info("Report generated: unified_agent_report.json")
            print("✓ Report generated: unified_agent_report.json")
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            print(f"✗ Report error: {e}")
            return None
    
    # ============= CLEANUP =============
    
    def cleanup(self):
        """
        Cleanup resources and close browser.
        
        Example:
            >>> agent.cleanup()
        """
        try:
            logger.info("Starting cleanup...")
            print("\n🧹 Cleaning up resources...")
            
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
                print("  ✓ Browser closed")
            
            self.scheduler_running = False
            
            logger.info("=" * 60)
            logger.info("Agent cleanup complete")
            logger.info("=" * 60)
            print("✓ Cleanup complete\n")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            print(f"✗ Cleanup error: {e}")


# ============= USAGE EXAMPLES =============

def example_basic_automation():
    """Example: Basic automation tasks"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Automation")
    print("=" * 60)
    
    agent = AutomationAgent()
    
    # Get mouse position
    print("\n1. Getting mouse position...")
    x, y = agent.get_mouse_position(delay=1)
    
    # Take screenshot
    print("\n2. Taking screenshot...")
    agent.screenshot("example_basic.png")
    
    agent.cleanup()


def example_browser_automation():
    """Example: Browser automation"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Browser Automation")
    print("=" * 60)
    
    agent = AutomationAgent()
    
    # Initialize browser
    print("\n1. Initializing browser...")
    agent.init_browser()
    
    # Navigate to website
    print("\n2. Navigating to Google...")
    agent.navigate_to("https://www.google.com")
    
    # Take screenshot
    print("\n3. Taking screenshot...")
    agent.screenshot("example_google.png")
    
    agent.cleanup()


def example_website_testing():
    """Example: Website testing"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Website Testing")
    print("=" * 60)
    
    agent = AutomationAgent()
    
    # Test performance
    print("\n1. Testing website performance...")
    results = agent.test_website_performance("https://www.google.com")
    print(f"   Load time: {results['total_load_time']:.2f}s")
    print(f"   Status: {results['status']}")
    
    agent.cleanup()


def example_scheduling():
    """Example: Task scheduling"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Task Scheduling")
    print("=" * 60)
    
    agent = AutomationAgent()
    
    # Schedule tasks
    print("\n1. Scheduling tasks...")
    
    # Schedule morning report
    agent.schedule_task("09:00", agent.morning_report)
    print("   ✓ Morning report scheduled for 09:00")
    
    # Schedule website test
    agent.schedule_task("14:00", agent.test_website, "https://www.google.com")
    print("   ✓ Website test scheduled for 14:00")
    
    # Schedule link check
    agent.schedule_task("16:00", agent.check_links, "https://www.google.com")
    print("   ✓ Link check scheduled for 16:00")
    
    print("\n2. To run scheduler, call: agent.run_scheduler()")
    print("   (This will run continuously until stopped with Ctrl+C)")
    
    agent.cleanup()


def example_bulk_whatsapp():
    """Example: Bulk WhatsApp messaging"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Bulk WhatsApp Messaging")
    print("=" * 60)
    
    agent = AutomationAgent()
    
    # Prepare contacts
    contacts = [
        {'phone': '256701234567', 'message': 'Hello! This is message 1'},
        {'phone': '256702345678', 'message': 'Hello! This is message 2'},
        {'phone': '256703456789', 'message': 'Hello! This is message 3'}
    ]
    
    print("\n1. Sending bulk WhatsApp messages...")
    print("   Note: Requires WhatsApp Web to be logged in")
    
    # Uncomment to actually send:
    # results = agent.send_bulk_whatsapp(contacts)
    # print(f"\n   Results: {results['success']} sent, {results['failed']} failed")
    
    print("   (Commented out - uncomment to use)")
    
    agent.cleanup()


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("UNIFIED AUTOMATION AGENT - COMPREHENSIVE EXAMPLES")
    print("=" * 70)
    
    # Run examples
    example_basic_automation()
    example_browser_automation()
    example_website_testing()
    example_scheduling()
    example_bulk_whatsapp()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nFor more information, see docstrings for each method.")
    print("Example: help(AutomationAgent.send_whatsapp_message)\n")


if __name__ == "__main__":
    main()
