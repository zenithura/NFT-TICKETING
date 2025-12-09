#!/usr/bin/env python3
"""
Admin Panel Automated Testing Script
Tests all navigation items, pages, and buttons in the admin panel.
"""

import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

# ============================================================================
# CONFIGURATION
# ============================================================================

# Admin Panel URL
ADMIN_BASE_URL = "http://localhost:4201"
ADMIN_LOGIN_URL = f"{ADMIN_BASE_URL}/secure-admin/login"
ADMIN_DASHBOARD_URL = f"{ADMIN_BASE_URL}/secure-admin/dashboard"

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # Change if different

# Test Configuration
HEADLESS = False  # Set to False to see browser
TIMEOUT = 30000  # 30 seconds timeout
WAIT_AFTER_CLICK = 2000  # Wait 2 seconds after each click

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PageTestResult:
    """Result of testing a single page."""
    button: str
    status: str  # "working", "broken", "error"
    url: str
    errors: List[str]
    load_time_ms: Optional[int] = None
    http_status: Optional[int] = None
    elements_found: List[str] = None
    buttons_tested: int = 0
    buttons_working: int = 0
    buttons_broken: int = 0

    def __post_init__(self):
        if self.elements_found is None:
            self.elements_found = []


@dataclass
class TestReport:
    """Complete test report."""
    login_status: str
    login_error: Optional[str] = None
    tested_pages: List[Dict] = None
    total_pages: int = 0
    working_pages: int = 0
    broken_pages: int = 0
    total_buttons_tested: int = 0
    total_buttons_working: int = 0
    total_buttons_broken: int = 0
    test_duration_seconds: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if self.tested_pages is None:
            self.tested_pages = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('admin_panel_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# TESTING CLASS
# ============================================================================

class AdminPanelTester:
    """Main testing class for admin panel."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000, 
                 admin_base_url: str = None, admin_login_url: str = None,
                 admin_username: str = None, admin_password: str = None):
        self.headless = headless
        self.timeout = timeout
        self.admin_base_url = admin_base_url or ADMIN_BASE_URL
        self.admin_login_url = admin_login_url or ADMIN_LOGIN_URL
        self.admin_username = admin_username or ADMIN_USERNAME
        self.admin_password = admin_password or ADMIN_PASSWORD
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.report = TestReport(login_status="not_started")
        self.start_time = None
        
    def setup(self):
        """Initialize Playwright and browser."""
        logger.info("Setting up Playwright...")
        self.playwright = sync_playwright().start()
        
        # Try to launch Playwright's Chromium first
        try:
            logger.info("Attempting to launch Playwright Chromium...")
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            logger.info("Playwright Chromium launched successfully")
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Playwright Chromium not available: {error_msg}")
            
            # Try to install Playwright Chromium
            if "Executable doesn't exist" in error_msg or "BrowserType.launch" in error_msg:
                logger.info("Attempting to install Playwright Chromium...")
                import subprocess
                import sys
                import os
                
                try:
                    # Try multiple installation methods
                    install_cmd = [sys.executable, '-m', 'playwright', 'install', 'chromium']
                    logger.info(f"Running: {' '.join(install_cmd)}")
                    
                    result = subprocess.run(
                        install_cmd,
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    if result.returncode == 0:
                        logger.info("Playwright Chromium installed successfully. Retrying launch...")
                        self.browser = self.playwright.chromium.launch(
                            headless=self.headless,
                            args=['--no-sandbox', '--disable-dev-shm-usage']
                        )
                        logger.info("Playwright Chromium launched successfully after installation")
                    else:
                        logger.warning(f"Installation command returned code {result.returncode}")
                        logger.warning(f"Output: {result.stdout}")
                        logger.warning(f"Error: {result.stderr}")
                        raise Exception("Failed to install Playwright Chromium")
                        
                except subprocess.TimeoutExpired:
                    logger.error("Installation timed out. Please run manually: python -m playwright install chromium")
                    raise Exception("Browser installation timed out")
                except Exception as install_error:
                    logger.error(f"Failed to install Playwright Chromium: {install_error}")
                    
                    # Try to use system Chromium as fallback
                    logger.info("Attempting to use system Chromium as fallback...")
                    system_chromium_paths = [
                        '/usr/bin/chromium',
                        '/usr/bin/chromium-browser',
                        '/snap/bin/chromium',
                        '/usr/bin/google-chrome',
                        '/usr/bin/google-chrome-stable'
                    ]
                    
                    chromium_path = None
                    for path in system_chromium_paths:
                        if os.path.exists(path):
                            chromium_path = path
                            logger.info(f"Found system Chromium at: {chromium_path}")
                            break
                    
                    if chromium_path:
                        try:
                            logger.info("Launching system Chromium...")
                            self.browser = self.playwright.chromium.launch(
                                headless=self.headless,
                                executable_path=chromium_path,
                                args=['--no-sandbox', '--disable-dev-shm-usage']
                            )
                            logger.info("System Chromium launched successfully")
                        except Exception as system_error:
                            logger.error(f"Failed to launch system Chromium: {system_error}")
                            raise Exception(
                                "Could not launch browser. Please install Playwright Chromium:\n"
                                "  python -m playwright install chromium\n"
                                "Or ensure system Chromium is installed and accessible."
                            )
                    else:
                        logger.error("No system Chromium found")
                        raise Exception(
                            "Browser not available. Please install Playwright Chromium:\n"
                            "  python -m playwright install chromium"
                        )
            else:
                raise
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        # Listen for console errors
        self.page.on("console", self._handle_console)
        self.page.on("pageerror", self._handle_page_error)
        
        logger.info("Browser initialized successfully")
        
    def _handle_console(self, msg):
        """Handle console messages."""
        if msg.type == "error":
            logger.warning(f"Console error: {msg.text}")
            
    def _handle_page_error(self, error):
        """Handle page errors."""
        logger.error(f"Page error: {error}")
        
    def login(self) -> Tuple[bool, Optional[str]]:
        """Login to admin panel."""
        logger.info(f"Navigating to login page: {self.admin_login_url}")
        self.start_time = time.time()
        
        try:
            # Navigate to login page
            response = self.page.goto(self.admin_login_url, wait_until="networkidle")
            
            if response and response.status >= 400:
                error = f"Login page returned HTTP {response.status}"
                logger.error(error)
                self.report.login_status = "failed"
                self.report.login_error = error
                return False, error
            
            # Wait for login form
            logger.info("Waiting for login form...")
            self.page.wait_for_selector("input[type='text'], input[type='email'], input[name='username']", timeout=10000)
            
            # Find username and password fields
            username_selectors = [
                "input[name='username']",
                "input[type='text']",
                "input[placeholder*='username' i]",
                "input[placeholder*='email' i]",
                "#username",
                ".username-input"
            ]
            
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "#password",
                ".password-input"
            ]
            
            username_field = None
            password_field = None
            
            for selector in username_selectors:
                try:
                    username_field = self.page.query_selector(selector)
                    if username_field:
                        break
                except:
                    continue
                    
            for selector in password_selectors:
                try:
                    password_field = self.page.query_selector(selector)
                    if password_field:
                        break
                except:
                    continue
            
            if not username_field or not password_field:
                error = "Could not find username or password fields"
                logger.error(error)
                self.report.login_status = "failed"
                self.report.login_error = error
                return False, error
            
            # Fill in credentials
            logger.info(f"Entering username: {self.admin_username}")
            username_field.fill(self.admin_username)
            time.sleep(0.5)
            
            logger.info("Entering password...")
            password_field.fill(self.admin_password)
            time.sleep(0.5)
            
            # Find and click login button
            login_button_selectors = [
                "button[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign in')",
                "button:has-text('Log in')",
                "#login-button",
                ".login-button",
                "input[type='submit']"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = self.page.query_selector(selector)
                    if login_button:
                        break
                except:
                    continue
            
            if not login_button:
                error = "Could not find login button"
                logger.error(error)
                self.report.login_status = "failed"
                self.report.login_error = error
                return False, error
            
            # Click login button
            logger.info("Clicking login button...")
            login_button.click()
            
            # Wait for navigation
            logger.info("Waiting for dashboard to load...")
            try:
                # Wait for URL to change or dashboard elements
                self.page.wait_for_url(
                    lambda url: "dashboard" in url or "login" not in url,
                    timeout=15000
                )
                
                # Check if we're still on login page (login failed)
                current_url = self.page.url
                if "login" in current_url.lower():
                    # Check for error messages
                    error_selectors = [
                        ".error",
                        ".alert-error",
                        "[role='alert']",
                        ".text-red",
                        ".text-error"
                    ]
                    
                    error_message = "Login failed - still on login page"
                    for selector in error_selectors:
                        try:
                            error_elem = self.page.query_selector(selector)
                            if error_elem:
                                error_text = error_elem.inner_text()
                                if error_text:
                                    error_message = f"Login failed: {error_text}"
                                    break
                        except:
                            continue
                    
                    logger.error(error_message)
                    self.report.login_status = "failed"
                    self.report.login_error = error_message
                    return False, error_message
                
                # Wait for dashboard to be ready
                self.page.wait_for_load_state("networkidle", timeout=10000)
                
                logger.info("Login successful!")
                self.report.login_status = "success"
                return True, None
                
            except PlaywrightTimeoutError:
                error = "Timeout waiting for dashboard to load"
                logger.error(error)
                self.report.login_status = "failed"
                self.report.login_error = error
                return False, error
                
        except Exception as e:
            error = f"Login error: {str(e)}"
            logger.error(error, exc_info=True)
            self.report.login_status = "failed"
            self.report.login_error = error
            return False, error
    
    def find_navigation_items(self) -> List[Dict[str, str]]:
        """Find all navigation items in the sidebar."""
        logger.info("Finding navigation items...")
        nav_items = []
        
        try:
            # Common navigation selectors
            nav_selectors = [
                "nav a",
                "aside a",
                ".sidebar a",
                ".nav a",
                "[role='navigation'] a",
                ".menu a",
                "nav button",
                "aside button",
                ".sidebar button",
                "[data-testid*='nav']",
                "[data-testid*='menu']"
            ]
            
            found_elements = set()
            
            for selector in nav_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            text = elem.inner_text().strip()
                            href = elem.get_attribute("href") or ""
                            
                            # Skip empty or duplicate items
                            if not text or (text, href) in found_elements:
                                continue
                            
                            # Skip common non-navigation items
                            skip_texts = ["logout", "log out", "sign out", "profile", "settings"]
                            if any(skip in text.lower() for skip in skip_texts):
                                continue
                            
                            found_elements.add((text, href))
                            nav_items.append({
                                "text": text,
                                "href": href,
                                "selector": selector
                            })
                        except:
                            continue
                except:
                    continue
            
            # Also look for tab buttons (common in admin dashboards)
            tab_selectors = [
                "button[role='tab']",
                ".tab",
                "[data-tab]",
                "button:has-text('Overview')",
                "button:has-text('Alerts')",
                "button:has-text('Users')",
                "button:has-text('Web Requests')",
                "button:has-text('SOAR')"
            ]
            
            for selector in tab_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            text = elem.inner_text().strip()
                            if text and (text, "") not in found_elements:
                                found_elements.add((text, ""))
                                nav_items.append({
                                    "text": text,
                                    "href": "",
                                    "selector": selector
                                })
                        except:
                            continue
                except:
                    continue
            
            # Remove duplicates
            unique_items = []
            seen_texts = set()
            for item in nav_items:
                if item["text"] not in seen_texts:
                    seen_texts.add(item["text"])
                    unique_items.append(item)
            
            logger.info(f"Found {len(unique_items)} navigation items: {[item['text'] for item in unique_items]}")
            return unique_items
            
        except Exception as e:
            logger.error(f"Error finding navigation items: {e}", exc_info=True)
            return []
    
    def test_page(self, nav_item: Dict[str, str]) -> PageTestResult:
        """Test a single page."""
        button_name = nav_item["text"]
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing page: {button_name}")
        logger.info(f"{'='*60}")
        
        result = PageTestResult(
            button=button_name,
            status="error",
            url="",
            errors=[]
        )
        
        try:
            # Click the navigation item
            start_time = time.time()
            
            # Try to find and click the element
            clicked = False
            for selector in [nav_item["selector"], f"button:has-text('{button_name}')", f"a:has-text('{button_name}')"]:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        element.click()
                        clicked = True
                        time.sleep(WAIT_AFTER_CLICK / 1000)
                        break
                except:
                    continue
            
            if not clicked:
                result.errors.append(f"Could not click navigation item: {button_name}")
                result.status = "broken"
                return result
            
            # Wait for page to load
            try:
                self.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass  # Continue even if networkidle times out
            
            # Get current URL
            current_url = self.page.url
            result.url = current_url
            
            # Check for errors
            load_time = int((time.time() - start_time) * 1000)
            result.load_time_ms = load_time
            
            # Check HTTP status (if available from response)
            try:
                response = self.page.wait_for_response(
                    lambda r: r.url == current_url or current_url in r.url,
                    timeout=5000
                )
                if response:
                    result.http_status = response.status
                    if response.status >= 400:
                        result.errors.append(f"HTTP {response.status} error")
                        result.status = "broken"
            except:
                pass  # Response might not be available
            
            # Check for error messages on page
            error_selectors = [
                ".error",
                ".alert-error",
                "[role='alert']:has-text('error')",
                ".text-red-500",
                ".text-error",
                "h1:has-text('404')",
                "h1:has-text('500')",
                "h1:has-text('Error')"
            ]
            
            for selector in error_selectors:
                try:
                    error_elem = self.page.query_selector(selector)
                    if error_elem:
                        error_text = error_elem.inner_text().strip()
                        if error_text:
                            result.errors.append(f"Page error: {error_text}")
                            result.status = "broken"
                except:
                    continue
            
            # Check for expected elements
            expected_elements = [
                "table",
                "form",
                "button",
                "input",
                "[data-testid]",
                ".content",
                "main",
                "article"
            ]
            
            for selector in expected_elements:
                try:
                    elem = self.page.query_selector(selector)
                    if elem:
                        result.elements_found.append(selector)
                except:
                    continue
            
            # Test buttons/links on this page
            buttons_result = self.test_page_buttons(button_name)
            result.buttons_tested = buttons_result["total"]
            result.buttons_working = buttons_result["working"]
            result.buttons_broken = buttons_result["broken"]
            
            if result.buttons_broken > 0:
                result.errors.extend(buttons_result["errors"])
            
            # Determine final status
            if not result.errors and result.http_status and result.http_status < 400:
                result.status = "working"
            elif result.errors:
                result.status = "broken"
            else:
                result.status = "working"  # Assume working if no errors found
            
            logger.info(f"Page test result: {result.status.upper()}")
            if result.errors:
                logger.warning(f"Errors found: {result.errors}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error testing page: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            result.status = "error"
            return result
    
    def test_page_buttons(self, page_name: str) -> Dict:
        """Test all buttons/links on a page."""
        logger.info(f"  Testing buttons on {page_name}...")
        result = {
            "total": 0,
            "working": 0,
            "broken": 0,
            "errors": []
        }
        
        try:
            # Find all clickable elements
            button_selectors = [
                "button:not([disabled])",
                "a[href]",
                "[role='button']:not([disabled])",
                ".btn:not([disabled])",
                "input[type='button']:not([disabled])",
                "input[type='submit']:not([disabled])"
            ]
            
            buttons = []
            for selector in button_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            text = elem.inner_text().strip()
                            if text and len(text) < 100:  # Skip very long text
                                buttons.append(elem)
                        except:
                            continue
                except:
                    continue
            
            # Remove duplicates
            unique_buttons = []
            seen_texts = set()
            for btn in buttons:
                try:
                    text = btn.inner_text().strip()
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        unique_buttons.append(btn)
                except:
                    continue
            
            result["total"] = len(unique_buttons)
            logger.info(f"  Found {len(unique_buttons)} buttons to test")
            
            # Test each button (limit to first 10 to avoid too many tests)
            for i, btn in enumerate(unique_buttons[:10]):
                try:
                    btn_text = btn.inner_text().strip()
                    logger.info(f"    Testing button: {btn_text}")
                    
                    # Get current URL before click
                    url_before = self.page.url
                    
                    # Click button
                    btn.click()
                    time.sleep(1)  # Wait for action
                    
                    # Check if something happened
                    url_after = self.page.url
                    
                    # Check for errors
                    has_error = False
                    error_selectors = [
                        ".error",
                        "[role='alert']:has-text('error')",
                        ".alert-danger"
                    ]
                    
                    for selector in error_selectors:
                        try:
                            error_elem = self.page.query_selector(selector)
                            if error_elem:
                                has_error = True
                                error_text = error_elem.inner_text().strip()
                                result["errors"].append(f"Button '{btn_text}': {error_text}")
                                break
                        except:
                            continue
                    
                    if not has_error:
                        result["working"] += 1
                    else:
                        result["broken"] += 1
                    
                    # Go back if URL changed
                    if url_after != url_before:
                        self.page.go_back()
                        time.sleep(1)
                    
                except Exception as e:
                    result["broken"] += 1
                    result["errors"].append(f"Button test error: {str(e)}")
                    logger.warning(f"    Button test failed: {e}")
            
        except Exception as e:
            logger.error(f"Error testing buttons: {e}", exc_info=True)
            result["errors"].append(f"Error testing buttons: {str(e)}")
        
        return result
    
    def run_tests(self):
        """Run all tests."""
        try:
            # Setup
            self.setup()
            
            # Login
            login_success, login_error = self.login()
            if not login_success:
                logger.error("Login failed. Stopping tests.")
                return
            
            # Find navigation items
            nav_items = self.find_navigation_items()
            
            if not nav_items:
                logger.warning("No navigation items found. Testing current page only.")
                nav_items = [{"text": "Current Page", "href": self.page.url, "selector": "body"}]
            
            # Test each page
            for nav_item in nav_items:
                result = self.test_page(nav_item)
                self.report.tested_pages.append(asdict(result))
                
                # Update counters
                if result.status == "working":
                    self.report.working_pages += 1
                else:
                    self.report.broken_pages += 1
                
                self.report.total_buttons_tested += result.buttons_tested
                self.report.total_buttons_working += result.buttons_working
                self.report.total_buttons_broken += result.buttons_broken
                
                # Small delay between pages
                time.sleep(1)
            
            # Calculate totals
            self.report.total_pages = len(self.report.tested_pages)
            self.report.test_duration_seconds = time.time() - self.start_time
            
            logger.info("\n" + "="*60)
            logger.info("All tests completed!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Test execution error: {e}", exc_info=True)
            self.report.login_error = f"Test execution error: {str(e)}"
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def generate_report(self) -> Dict:
        """Generate test report."""
        return asdict(self.report)
    
    def print_summary(self):
        """Print human-readable summary."""
        print("\n" + "="*60)
        print("ADMIN PANEL TEST REPORT")
        print("="*60)
        
        # Login status
        login_icon = "✓" if self.report.login_status == "success" else "✗"
        print(f"\nLogin: {login_icon} {self.report.login_status.upper()}")
        if self.report.login_error:
            print(f"  Error: {self.report.login_error}")
        
        # Summary
        print(f"\nTotal Pages: {self.report.total_pages}")
        print(f"Working: {self.report.working_pages}")
        print(f"Broken: {self.report.broken_pages}")
        print(f"\nTotal Buttons Tested: {self.report.total_buttons_tested}")
        print(f"Working Buttons: {self.report.total_buttons_working}")
        print(f"Broken Buttons: {self.report.total_buttons_broken}")
        print(f"\nTest Duration: {self.report.test_duration_seconds:.2f} seconds")
        
        # Broken pages
        broken_pages = [p for p in self.report.tested_pages if p["status"] != "working"]
        if broken_pages:
            print("\n" + "-"*60)
            print("Broken Pages:")
            print("-"*60)
            for page in broken_pages:
                print(f"\n- {page['button']}")
                print(f"  Status: {page['status']}")
                print(f"  URL: {page['url']}")
                if page['errors']:
                    print(f"  Errors:")
                    for error in page['errors']:
                        print(f"    • {error}")
        
        print("\n" + "="*60)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Admin Panel Automated Testing")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Show browser window")
    parser.add_argument("--url", type=str, default=None, help="Admin panel base URL")
    parser.add_argument("--username", type=str, default=None, help="Admin username")
    parser.add_argument("--password", type=str, default=None, help="Admin password")
    parser.add_argument("--output", type=str, default="admin_test_report.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    # Use provided args or defaults
    admin_base_url = args.url if args.url else ADMIN_BASE_URL
    admin_username = args.username if args.username else ADMIN_USERNAME
    admin_password = args.password if args.password else ADMIN_PASSWORD
    admin_login_url = f"{admin_base_url}/secure-admin/login"
    admin_dashboard_url = f"{admin_base_url}/secure-admin/dashboard"
    
    # Create tester with custom config
    tester = AdminPanelTester(
        headless=args.headless,
        admin_base_url=admin_base_url,
        admin_login_url=admin_login_url,
        admin_username=admin_username,
        admin_password=admin_password
    )
    
    # Run tests
    tester.run_tests()
    
    # Generate report
    report = tester.generate_report()
    
    # Save JSON report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"\nReport saved to: {args.output}")
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    main()

