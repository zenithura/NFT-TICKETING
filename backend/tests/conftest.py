"""Pytest configuration and fixtures."""
# Prevent web3 pytest plugin from loading (causes eth_typing compatibility issues)
import sys
from types import ModuleType

# Mock web3.tools modules before pytest tries to load the plugin
# This must happen before any imports that might trigger plugin loading
web3_tools = ModuleType('web3.tools')
web3_pytest = ModuleType('web3.tools.pytest_ethereum')
web3_plugins = ModuleType('web3.tools.pytest_ethereum.plugins')
web3_deployer = ModuleType('web3.tools.pytest_ethereum.deployer')

sys.modules['web3.tools'] = web3_tools
sys.modules['web3.tools.pytest_ethereum'] = web3_pytest
sys.modules['web3.tools.pytest_ethereum.plugins'] = web3_plugins
sys.modules['web3.tools.pytest_ethereum.deployer'] = web3_deployer

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "http://localhost:54321")
os.environ["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY", "test-key")
os.environ["SUPABASE_SERVICE_KEY"] = os.getenv("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ["JWT_SECRET"] = os.getenv("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["JWT_REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

@pytest.fixture(scope="module")
def client():
    """Create test client for FastAPI app."""
    from main import app
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_db():
    """Mock Supabase database client."""
    mock_db = Mock()
    mock_db.table.return_value = Mock()
    return mock_db

@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "email": "test@example.com",
        "password": "Test123!@#",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "role": "BUYER"
    }

@pytest.fixture
def test_event_data():
    """Test event data fixture."""
    return {
        "name": "Test Concert",
        "description": "A test event for integration testing",
        "date": "2025-12-31T20:00:00Z",
        "location": "Test Venue, Test City",
        "total_tickets": 100,
        "price": 0.05,
        "currency": "ETH",
        "category": "Music",
        "image_url": "https://example.com/image.jpg"
    }

@pytest.fixture
def auth_headers(client, test_user_data):
    """Get authentication headers by registering and logging in."""
    # Register user
    register_response = client.post(
        "/api/auth/register",
        json=test_user_data
    )
    
    if register_response.status_code == 201:
        access_token = register_response.json().get("access_token")
    else:
        # Try login if user already exists
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        if login_response.status_code == 200:
            access_token = login_response.json().get("access_token")
        else:
            access_token = None
    
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}

@pytest.fixture
def organizer_auth_headers(client):
    """Get authentication headers for organizer role."""
    organizer_data = {
        "email": "organizer@example.com",
        "password": "Organizer123!@#",
        "username": "organizer",
        "first_name": "Event",
        "last_name": "Organizer",
        "role": "ORGANIZER"
    }
    
    # Register organizer
    register_response = client.post(
        "/api/auth/register",
        json=organizer_data
    )
    
    if register_response.status_code == 201:
        access_token = register_response.json().get("access_token")
    else:
        # Try login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": organizer_data["email"],
                "password": organizer_data["password"]
            }
        )
        if login_response.status_code == 200:
            access_token = login_response.json().get("access_token")
        else:
            access_token = None
    
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}

@pytest.fixture
def admin_auth_headers(client):
    """Get authentication headers for admin role."""
    # This would typically require admin login endpoint
    # For now, return empty headers - admin tests will need proper setup
    return {}

