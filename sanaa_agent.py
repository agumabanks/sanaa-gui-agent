"""
Advanced ML-Powered Computer Automation Agent
Handles screen control, browser automation, testing, and scheduling
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
from PIL import Image
import cv2
import numpy as np
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_log.txt'),
        logging.StreamHandler()
    ]
)

class AutomationAgent:
    """Main automation agent with ML capabilities"""
    
    def __init__(self):
        self.system = platform.system()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self.actions_log = []
        self.driver = None
        logging.info("Agent initialized")
        
    # ============= SCREEN CONTROL =============
    
    def click(self, x, y):
        """Click at coordinates"""
        logging.info(f"Clicking at ({x}, {y})")
        pyautogui.click(x, y)
        self.log_action(f"Click at ({x}, {y})")
        
    def type_text(self, text, interval=0.05):
        """Type text"""
        logging.info(f"Typing: {text}")
        pyautogui.write(text, interval=interval)
        self.log_action(f"Typed: {text}")
        
    def press_key(self, key):
        """Press keyboard key"""
        pyautogui.press(key)
        self.log_action(f"Pressed key: {key}")
        
    def hotkey(self, *keys):
        """Press key combination"""
        pyautogui.hotkey(*keys)
        self.log_action(f"Hotkey: {'+'.join(keys)}")
        
    def get_mouse_position(self):
        """Get current mouse position"""
        pos = pyautogui.position()
        logging.info(f"Mouse at: {pos}")
        return pos
    
    def screenshot(self, filename=None):
        """Take screenshot"""
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot(filename)
        logging.info(f"Screenshot saved: {filename}")
        self.log_action(f"Screenshot: {filename}")
        return filename
    
    def find_image_on_screen(self, image_path, confidence=0.8):
        """Find image on screen using template matching"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                logging.info(f"Found image at: {location}")
                return pyautogui.center(location)
            return None
        except Exception as e:
            logging.error(f"Image search failed: {e}")
            return None
    
    def click_image(self, image_path, confidence=0.8):
        """Find and click image"""
        pos = self.find_image_on_screen(image_path, confidence)
        if pos:
            self.click(pos.x, pos.y)
            return True
        logging.warning(f"Image not found: {image_path}")
        return False
    
    # ============= BROWSER AUTOMATION =============
    
    def init_browser(self, headless=False):
        """Initialize Selenium browser"""
        try:
            options = Options()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logging.info("Browser initialized")
            self.log_action("Browser opened")
            return True
        except Exception as e:
            logging.error(f"Browser init failed: {e}")
            return False
    
    def navigate_to(self, url):
        """Navigate to URL"""
        if not self.driver:
            self.init_browser()
        logging.info(f"Navigating to: {url}")
        self.driver.get(url)
        self.log_action(f"Navigated to: {url}")
        time.sleep(2)
    
    def find_element(self, by, value, timeout=10):
        """Find element with wait"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logging.error(f"Element not found: {value}")
            return None
    
    def click_element(self, by, value):
        """Click web element"""
        element = self.find_element(by, value)
        if element:
            element.click()
            self.log_action(f"Clicked element: {value}")
            return True
        return False
    
    def fill_form(self, field_data):
        """Fill form fields
        field_data: dict like {'name_field': 'John', 'email_field': 'john@example.com'}
        """
        for field_id, value in field_data.items():
            element = self.find_element(By.ID, field_id)
            if not element:
                element = self.find_element(By.NAME, field_id)
            if element:
                element.clear()
                element.send_keys(value)
                self.log_action(f"Filled {field_id}: {value}")
        logging.info("Form filled")
    
    def submit_form(self, button_id=None):
        """Submit form"""
        if button_id:
            self.click_element(By.ID, button_id)
        else:
            self.driver.find_element(By.TAG_NAME, 'form').submit()
        self.log_action("Form submitted")
    
    # ============= WEBSITE TESTING =============
    
    def test_website_performance(self, url):
        """Test website performance"""
        logging.info(f"Testing performance: {url}")
        
        if not self.driver:
            self.init_browser()
        
        # Measure load time
        start_time = time.time()
        self.navigate_to(url)
        load_time = time.time() - start_time
        
        # Get performance metrics
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
        
        self.log_action(f"Performance test: {results}")
        logging.info(f"Performance results: {results}")
        
        # Save results
        self.save_test_results(results)
        
        return results
    
    def test_form_submission(self, url, form_data, submit_button_id=None):
        """Test form submission"""
        logging.info(f"Testing form: {url}")
        
        try:
            self.navigate_to(url)
            time.sleep(2)
            
            self.fill_form(form_data)
            time.sleep(1)
            
            before_screenshot = self.screenshot("before_submit.png")
            
            self.submit_form(submit_button_id)
            time.sleep(3)
            
            after_screenshot = self.screenshot("after_submit.png")
            
            result = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'form_data': form_data,
                'status': 'success',
                'before_screenshot': before_screenshot,
                'after_screenshot': after_screenshot
            }
            
            self.log_action(f"Form test: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Form test failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def check_broken_links(self, url):
        """Check for broken links on page"""
        logging.info(f"Checking links on: {url}")
        
        self.navigate_to(url)
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        
        broken_links = []
        for link in links:
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
                except Exception as e:
                    broken_links.append({
                        'url': href,
                        'error': str(e),
                        'text': link.text
                    })
        
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'total_links': len(links),
            'broken_links': broken_links,
            'status': 'passed' if len(broken_links) == 0 else 'failed'
        }
        
        self.log_action(f"Link check: {result}")
        return result
    
    # ============= WHATSAPP AUTOMATION =============
    
    def send_whatsapp_message(self, phone_number, message):
        """Send WhatsApp message via Web"""
        logging.info(f"Sending WhatsApp to: {phone_number}")
        
        # Format URL
        message_encoded = requests.utils.quote(message)
        url = f"https://web.whatsapp.com/send?phone={phone_number}&text={message_encoded}"
        
        if not self.driver:
            self.init_browser()
        
        self.navigate_to(url)
        
        # Wait for WhatsApp to load
        time.sleep(15)
        
        try:
            # Wait for send button and click
            send_button = self.find_element(By.XPATH, '//span[@data-icon="send"]', timeout=20)
            if send_button:
                send_button.click()
                logging.info("WhatsApp message sent")
                self.log_action(f"WhatsApp sent to {phone_number}: {message}")
                return True
        except Exception as e:
            logging.error(f"WhatsApp send failed: {e}")
            # Fallback: press Enter
            try:
                pyautogui.press('enter')
                logging.info("WhatsApp message sent (fallback)")
                return True
            except:
                return False
        
        return False
    
    def schedule_whatsapp(self, time_str, phone_number, message):
        """Schedule WhatsApp message"""
        def job():
            self.send_whatsapp_message(phone_number, message)
        
        schedule.every().day.at(time_str).do(job)
        logging.info(f"WhatsApp scheduled for {time_str} to {phone_number}")
        self.log_action(f"Scheduled WhatsApp: {time_str} -> {phone_number}")
    
    # ============= WEB SEARCH =============
    
    def google_search(self, query):
        """Perform Google search"""
        logging.info(f"Searching: {query}")
        
        if not self.driver:
            self.init_browser()
        
        self.navigate_to("https://www.google.com")
        
        search_box = self.find_element(By.NAME, "q")
        if search_box:
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)
            
            self.log_action(f"Google search: {query}")
            
            # Get search results
            results = []
            try:
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
                for elem in result_elements[:5]:
                    try:
                        title = elem.find_element(By.CSS_SELECTOR, 'h3').text
                        link = elem.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                        results.append({'title': title, 'url': link})
                    except:
                        continue
            except Exception as e:
                logging.error(f"Could not parse results: {e}")
            
            return results
        
        return []
    
    # ============= APP CONTROL =============
    
    def open_app(self, app_name):
        """Open application"""
        logging.info(f"Opening: {app_name}")
        
        try:
            if self.system == "Windows":
                subprocess.Popen(["start", app_name], shell=True)
            elif self.system == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name.lower()])
            
            time.sleep(3)
            self.log_action(f"Opened app: {app_name}")
            return True
        except Exception as e:
            logging.error(f"Could not open {app_name}: {e}")
            return False
    
    # ============= TASK SCHEDULING =============
    
    def schedule_task(self, time_str, task_func, *args, **kwargs):
        """Schedule task at specific time"""
        def job():
            logging.info(f"Running scheduled task: {task_func.__name__}")
            task_func(*args, **kwargs)
        
        schedule.every().day.at(time_str).do(job)
        logging.info(f"Task scheduled: {task_func.__name__} at {time_str}")
        self.log_action(f"Scheduled: {task_func.__name__} at {time_str}")
    
    def run_scheduler(self):
        """Run scheduled tasks"""
        logging.info("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    # ============= LOGGING & RECORDING =============
    
    def log_action(self, action):
        """Log action to memory and file"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action
        }
        self.actions_log.append(entry)
        
        # Save to file
        with open('actions_log.json', 'w') as f:
            json.dump(self.actions_log, f, indent=2)
    
    def get_action_history(self, limit=None):
        """Get action history"""
        if limit:
            return self.actions_log[-limit:]
        return self.actions_log
    
    def save_test_results(self, results):
        """Save test results"""
        filename = 'test_results.json'
        
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
        
        logging.info(f"Test results saved to {filename}")
    
    def generate_report(self):
        """Generate activity report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_actions': len(self.actions_log),
            'recent_actions': self.actions_log[-10:] if self.actions_log else []
        }
        
        with open('agent_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info("Report generated: agent_report.json")
        return report
    
    # ============= CLEANUP =============
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
            logging.info("Browser closed")
        logging.info("Agent cleanup complete")


# ============= EXAMPLE USAGE =============

def main():
    """Example usage"""
    agent = AutomationAgent()
    
    # Example 1: Test website performance
    print("\n=== Testing Website Performance ===")
    results = agent.test_website_performance("https://www.google.com")
    print(f"Load time: {results['total_load_time']:.2f}s")
    print(f"Status: {results['status']}")
    
    # Example 2: Google search
    print("\n=== Performing Google Search ===")
    search_results = agent.google_search("Python automation")
    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result['title']}")
    
    # Example 3: Send WhatsApp (uncomment to use)
    # print("\n=== Sending WhatsApp ===")
    # agent.send_whatsapp_message("256701234567", "Hello from Agent!")
    
    # Example 4: Schedule WhatsApp message
    # agent.schedule_whatsapp("15:30", "256701234567", "Scheduled message!")
    
    # Example 5: Test form (example URL)
    # print("\n=== Testing Form ===")
    # form_data = {'name': 'Test User', 'email': 'test@example.com'}
    # agent.test_form_submission("https://example.com/form", form_data)
    
    # Example 6: Check for broken links
    # print("\n=== Checking Links ===")
    # link_results = agent.check_broken_links("https://example.com")
    # print(f"Broken links found: {len(link_results['broken_links'])}")
    
    # Generate report
    print("\n=== Generating Report ===")
    report = agent.generate_report()
    print(f"Total actions: {report['total_actions']}")
    
    # View action history
    print("\n=== Recent Actions ===")
    for action in agent.get_action_history(limit=5):
        print(f"{action['timestamp']}: {action['action']}")
    
    # Cleanup
    agent.cleanup()
    
    # To run scheduler (uncomment):
    # agent.run_scheduler()


if __name__ == "__main__":
    main()