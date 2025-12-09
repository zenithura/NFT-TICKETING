# Admin Panel Automated Testing Script

Complete Python automation script using Playwright to test the admin panel.

## Features

✅ **Automatic Login Testing**
- Tests admin login with credentials
- Detects login failures and errors
- Waits for dashboard to load

✅ **Navigation Detection**
- Automatically finds all navigation items in sidebar
- Detects tabs, buttons, and links
- Handles different UI patterns

✅ **Page Testing**
- Tests each navigation item
- Checks for HTTP errors (404, 500, etc.)
- Detects JavaScript errors
- Validates page elements
- Measures load times

✅ **Button/Link Testing**
- Finds all clickable elements on each page
- Tests each button/link
- Detects crashes and errors
- Automatically navigates back

✅ **Comprehensive Reporting**
- JSON report with all details
- Human-readable console summary
- Error logging to file

## Installation

### 1. Install Python Dependencies

```bash
pip install playwright
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

Or install all browsers:
```bash
playwright install
```

## Usage

### Basic Usage

```bash
python admin_panel_test.py
```

### With Options

```bash
# Show browser window (not headless)
python admin_panel_test.py --no-headless

# Custom URL
python admin_panel_test.py --url http://localhost:4201

# Custom credentials
python admin_panel_test.py --username admin --password Admin123!

# Custom output file
python admin_panel_test.py --output my_report.json
```

### All Options

```bash
python admin_panel_test.py --help
```

Options:
- `--headless`: Run in headless mode (default: True)
- `--no-headless`: Show browser window
- `--url`: Admin panel base URL (default: http://localhost:4201)
- `--username`: Admin username (default: admin)
- `--password`: Admin password (default: admin)
- `--output`: Output JSON file (default: admin_test_report.json)

## Configuration

Edit the script to change defaults:

```python
# Admin Panel URL
ADMIN_BASE_URL = "http://localhost:4201"
ADMIN_LOGIN_URL = f"{ADMIN_BASE_URL}/secure-admin/login"

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Test Configuration
HEADLESS = True  # Set to False to see browser
TIMEOUT = 30000  # 30 seconds timeout
WAIT_AFTER_CLICK = 2000  # Wait 2 seconds after each click
```

## Output

### JSON Report

The script generates a detailed JSON report:

```json
{
  "login_status": "success",
  "tested_pages": [
    {
      "button": "Overview",
      "status": "working",
      "url": "http://localhost:4201/secure-admin/dashboard#/",
      "errors": [],
      "load_time_ms": 1234,
      "http_status": 200,
      "elements_found": ["table", "button"],
      "buttons_tested": 5,
      "buttons_working": 5,
      "buttons_broken": 0
    },
    {
      "button": "Alerts",
      "status": "broken",
      "url": "http://localhost:4201/secure-admin/dashboard#/alerts",
      "errors": ["HTTP 500 error"],
      "load_time_ms": 5000,
      "http_status": 500
    }
  ],
  "total_pages": 2,
  "working_pages": 1,
  "broken_pages": 1,
  "test_duration_seconds": 45.67,
  "timestamp": "2025-12-09T12:34:56.789Z"
}
```

### Console Summary

```
==============================
ADMIN PANEL TEST REPORT
==============================

Login: ✓ SUCCESS

Total Pages: 5
Working: 4
Broken: 1

Total Buttons Tested: 23
Working Buttons: 21
Broken Buttons: 2

Test Duration: 45.67 seconds

------------------------------
Broken Pages:
------------------------------

- Settings
  Status: broken
  URL: http://localhost:4201/secure-admin/dashboard#/settings
  Errors:
    • HTTP 500 error
    • Page error: Internal Server Error
==============================
```

### Log File

All test activities are logged to `admin_panel_test.log`:

```
2025-12-09 12:34:56 - INFO - Setting up Playwright...
2025-12-09 12:34:57 - INFO - Browser initialized successfully
2025-12-09 12:34:57 - INFO - Navigating to login page: http://localhost:4201/secure-admin/login
2025-12-09 12:34:58 - INFO - Login successful!
2025-12-09 12:34:59 - INFO - Found 5 navigation items: ['Overview', 'Alerts', 'Users', 'Web Requests', 'SOAR']
...
```

## How It Works

1. **Setup**: Initializes Playwright and browser
2. **Login**: Navigates to login page, fills credentials, submits
3. **Navigation Detection**: Finds all navigation items automatically
4. **Page Testing**: For each navigation item:
   - Clicks the item
   - Waits for page load
   - Checks for errors
   - Validates elements
   - Tests buttons/links
5. **Reporting**: Generates JSON and console reports

## Error Handling

The script handles:
- ✅ Login failures
- ✅ Page load timeouts
- ✅ HTTP errors (404, 500, etc.)
- ✅ JavaScript errors
- ✅ Missing elements
- ✅ Network issues
- ✅ Button click failures

## Troubleshooting

### Browser Not Found

```bash
playwright install chromium
```

### Login Fails

1. Check credentials in script or command line
2. Verify admin panel URL is correct
3. Check if admin panel is running
4. Run with `--no-headless` to see what's happening

### No Navigation Items Found

1. Check if you're logged in successfully
2. Verify the dashboard loaded
3. Run with `--no-headless` to inspect the page
4. The script will test the current page if no nav items found

### Timeout Errors

Increase timeout in script:
```python
TIMEOUT = 60000  # 60 seconds
```

## Example Output

```bash
$ python admin_panel_test.py --no-headless

2025-12-09 12:34:56 - INFO - Setting up Playwright...
2025-12-09 12:34:57 - INFO - Browser initialized successfully
2025-12-09 12:34:57 - INFO - Navigating to login page...
2025-12-09 12:34:58 - INFO - Login successful!
2025-12-09 12:34:59 - INFO - Found 5 navigation items: ['Overview', 'Alerts', 'Users', 'Web Requests', 'SOAR']

============================================================
Testing page: Overview
============================================================
  Testing buttons on Overview...
    Found 3 buttons to test
    Testing button: Refresh
    Testing button: Export
    Testing button: Clear
Page test result: WORKING

============================================================
Testing page: Alerts
============================================================
  Testing buttons on Alerts...
    Found 8 buttons to test
    Testing button: Export JSON
    Testing button: Export CSV
    Testing button: Clear All Alerts
Page test result: WORKING

...

============================================================
All tests completed!
============================================================

Report saved to: admin_test_report.json

==============================
ADMIN PANEL TEST REPORT
==============================

Login: ✓ SUCCESS

Total Pages: 5
Working: 5
Broken: 0

Total Buttons Tested: 23
Working Buttons: 23
Broken Buttons: 0

Test Duration: 45.67 seconds

==============================
```

## Requirements

- Python 3.10+
- Playwright 1.40.0+
- Chromium browser (installed via Playwright)

## License

Part of the NFT Ticketing Platform project.

