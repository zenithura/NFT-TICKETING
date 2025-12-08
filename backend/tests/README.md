# Backend Test Suite

## Overview

Comprehensive test suite for the FastAPI backend using pytest.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── test_health.py       # Health check tests
├── test_auth.py         # Authentication endpoint tests
├── test_events.py       # Event management tests
├── test_tickets.py      # Ticket management tests
├── test_marketplace.py  # Marketplace tests
├── test_wallet.py       # Wallet connection tests
├── test_admin.py        # Admin endpoint tests
└── test_e2e_flows.py    # End-to-end flow tests
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Specific Test File
```bash
pytest tests/test_auth.py -v
```

### By Marker
```bash
pytest tests/ -m integration -v
pytest tests/ -m unit -v
pytest tests/ -m e2e -v
```

## Test Fixtures

- `client`: FastAPI test client
- `test_user_data`: Sample user data
- `test_event_data`: Sample event data
- `auth_headers`: Authentication headers
- `organizer_auth_headers`: Organizer authentication headers
- `admin_auth_headers`: Admin authentication headers

## Writing New Tests

```python
import pytest

@pytest.mark.integration
def test_new_endpoint(client):
    """Test new endpoint."""
    response = client.get("/api/new-endpoint")
    assert response.status_code == 200
```

