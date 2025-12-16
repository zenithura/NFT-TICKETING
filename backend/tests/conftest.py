"""Pytest configuration and shared fixtures."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from typing import Generator
import os
import sys

# Set test environment variables before imports
os.environ["TESTING"] = "1"
os.environ["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "https://test.supabase.co")
os.environ["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRlc3QiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0NTk2ODgwMCwiZXhwIjo5OTk5OTk5OTk5fQ.test")
os.environ["SUPABASE_SERVICE_KEY"] = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRlc3QiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjQ1OTY4ODAwLCJleHAiOjk5OTk5OTk5OTl9.test")
os.environ["JWT_SECRET"] = os.getenv("JWT_SECRET", "test-jwt-secret-key-for-testing-only-must-be-long-enough-32-chars")
os.environ["JWT_ALGORITHM"] = "HS256"

# Patch database before any imports
mock_db_instance = Mock()
mock_table_instance = Mock()
mock_response_instance = Mock()

def create_mock_table():
    """Create a properly chained mock table."""
    table = Mock()
    response = Mock()
    response.data = []
    
    # Chain all methods
    chain_methods = ['select', 'insert', 'update', 'delete', 'eq', 'neq', 'gt', 'gte', 
                     'lt', 'lte', 'limit', 'order', 'is_', 'like', 'ilike', 'in_', 
                     'contains', 'contained_by', 'range', 'single']
    for method in chain_methods:
        setattr(table, method, Mock(return_value=table))
    
    table.execute = Mock(return_value=response)
    return table, response

mock_table_instance, mock_response_instance = create_mock_table()
# Create a mock function for dependencies to avoid FastAPI signature inspection issues with Mock objects
def mock_get_db():
    return mock_db_instance

# Patch database module completely
with patch('database.create_client', return_value=mock_db_instance), \
     patch('database.get_supabase', new=mock_get_db), \
     patch('database.get_supabase_admin', new=mock_get_db):
    # Also patch the module-level clients
    import database
    database.supabase = mock_db_instance
    database.supabase_admin = mock_db_instance
    
    # Patch security middleware BEFORE importing main
    # Patch security middleware BEFORE importing main
    # We mock is_banned because it makes DB calls that interfere with test mocks (side_effects).
    # We do NOT mock detection functions, so we can test them.
    import security_middleware
    security_middleware.is_banned = lambda db, user_id=None, ip_address=None: False
    
    # Patch WebRequestsMiddleware
    import web_requests_middleware
    # We need to patch the class method dispatch, but since it's an instance method called by BaseHTTPMiddleware,
    # it's safer to patch the class itself or the dispatch method on the class.
    # However, BaseHTTPMiddleware logic is complex.
    # Let's just patch the dispatch method.
    async def bypass_dispatch(self, request, call_next):
        return await call_next(request)
    web_requests_middleware.WebRequestsMiddleware.dispatch = bypass_dispatch

    # Now import main
    from main import app
    
    # Ensure middleware is using the patched version or remove it if already added
    # Since we patched the function in the module before main imported it (if main imports from module),
    # it should be fine. But main does `from security_middleware import security_middleware`.
    # If we patched `security_middleware.security_middleware`, main will import the patched one 
    # IF security_middleware was already imported.
    # To be safe, we can also patch it in main if needed, but main is imported here.



@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    global mock_db_instance, mock_table_instance, mock_response_instance
    mock_table_instance, mock_response_instance = create_mock_table()
    mock_db_instance.table = Mock(return_value=mock_table_instance)
    yield


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    return mock_db_instance


@pytest.fixture
def mock_supabase_table():
    """Mock Supabase table for testing."""
    return mock_table_instance


@pytest.fixture(autouse=True)
def mock_web3():
    """Mock Web3 client for testing."""
    with patch("web3_client.load_contracts"), \
         patch("web3_client.w3") as mock_w3, \
         patch("web3_client.contracts", {}), \
         patch("web3_client.send_transaction") as mock_send:
        
        # Mock transaction response
        mock_send.return_value = {"tx_hash": "0x123", "status": 1}
        
        yield


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Sample test user data."""
    return {
        "user_id": 1,
        "email": "test@example.com",
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "role": "BUYER",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "wallet_address": "0x1234567890123456789012345678901234567890",
        "is_email_verified": True,
        "is_active": True,
        "failed_login_attempts": 0,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def test_organizer():
    """Sample test organizer data."""
    return {
        "user_id": 2,
        "email": "organizer@example.com",
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "role": "ORGANIZER",
        "username": "organizer",
        "first_name": "Event",
        "last_name": "Organizer",
        "wallet_address": "0x2345678901234567890123456789012345678901",
        "is_email_verified": True,
        "is_active": True,
        "failed_login_attempts": 0,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def test_event():
    """Sample test event data."""
    return {
        "event_id": 1,
        "id": 1,
        "organizer_id": 2,
        "venue_id": 1,
        "name": "Test Event",
        "description": "Test Description",
        "event_date": "2024-12-31T20:00:00Z",
        "location": "Test Venue, Test City",
        "total_tickets": 100,
        "total_supply": 100,
        "available_tickets": 100,
        "price": 50.00,
        "base_price": 50.00,
        "category": "Music",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def test_ticket():
    """Sample test ticket data."""
    return {
        "ticket_id": 1,
        "id": 1,
        "event_id": 1,
        "owner_id": 1,
        "owner_address": "0x1234567890123456789012345678901234567890",
        "token_id": 123,
        "nft_token_id": 123,
        "price": 50.00,
        "status": "active",
        "for_sale": False,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def test_venue():
    """Sample venue data."""
    return {
        "venue_id": 1,
        "name": "Test Venue",
        "location": "Test Venue, Test City",
        "city": "Test City",
        "capacity": 100
    }


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user."""
    from auth_utils import create_access_token
    
    token = create_access_token({
        "sub": str(test_user["user_id"]), 
        "email": test_user["email"],
        "role": test_user["role"]
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def organizer_headers(test_organizer):
    """Generate authentication headers for organizer."""
    from auth_utils import create_access_token
    
    token = create_access_token({
        "sub": str(test_organizer["user_id"]), 
        "email": test_organizer["email"],
        "role": test_organizer["role"]
    })
    return {"Authorization": f"Bearer {token}"}
