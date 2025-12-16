# Backend Test Suite

## Overview

Comprehensive test suite for the NFT Ticketing Platform backend API. This test suite covers:

- Authentication and authorization
- Events management
- Ticket operations
- Marketplace functionality
- Wallet integration
- Security middleware
- Integration workflows

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_auth.py             # Authentication tests (register, login, password reset)
├── test_events.py           # Event CRUD operations
├── test_tickets.py          # Ticket purchase and management
├── test_marketplace.py      # Marketplace listing and purchasing
├── test_wallet.py           # Wallet connection and management
├── test_security_middleware.py  # Security features and middleware
└── test_integration.py      # End-to-end workflow tests
```

## Running Tests

### Run all tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py -v
```

### Run specific test
```bash
pytest tests/test_auth.py::TestAuthRegister::test_register_success -v
```

## Test Coverage

Current coverage: **~19%** (target: 80%+)

### Coverage by Component:
- Auth router: 14%
- Events router: 8%
- Tickets router: 10%
- Marketplace router: 13%
- Security middleware: 11%

## Fixtures

### Available Fixtures

- `client`: FastAPI test client
- `mock_supabase_client`: Mock Supabase database client
- `mock_supabase_table`: Mock Supabase table operations
- `test_user`: Sample user data
- `test_organizer`: Sample organizer data
- `test_event`: Sample event data
- `test_ticket`: Sample ticket data
- `auth_headers`: Authentication headers for regular user
- `organizer_headers`: Authentication headers for organizer

## Writing New Tests

### Example Test

```python
def test_example(self, client, auth_headers, mock_supabase_client):
    """Test example endpoint."""
    # Setup mocks
    mock_response = Mock()
    mock_response.data = [{"id": 1, "name": "Test"}]
    mock_supabase_client.table.return_value.execute.return_value = mock_response
    
    # Make request
    response = client.get("/api/endpoint", headers=auth_headers)
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

## Notes

- All external dependencies (Supabase, Web3) are mocked
- Tests run in isolated environment
- Test database connections are not required
- JWT tokens are generated for testing

## Future Improvements

- [ ] Increase coverage to 80%+
- [ ] Add load/stress testing
- [ ] Add Web3 integration tests with testnet
- [ ] Add database integration tests (optional)
- [ ] Add API contract testing

