"""Tests for authentication router."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import status
from datetime import datetime, timedelta, timezone


class TestAuthRegister:
    """Test user registration."""
    
    def test_register_success(self, client, mock_supabase_client):
        """Test successful user registration."""
        from unittest.mock import patch
        from database import get_supabase_admin
        
        # Mock: user doesn't exist
        check_response = Mock()
        check_response.data = []
        
        # Mock: insert successful
        insert_response = Mock()
        new_user = {
            "user_id": 1,
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "role": "BUYER",
            "is_email_verified": False,
            "created_at": "2024-01-01T00:00:00Z"
        }
        insert_response.data = [new_user]
        
        # Setup mock chain - need to properly chain the table calls
        mock_table = mock_supabase_client.table.return_value
        
        # Configure the mock to return different responses for different calls
        def mock_execute():
            if not hasattr(mock_execute, 'call_count'):
                mock_execute.call_count = 0
            mock_execute.call_count += 1
            
            if mock_execute.call_count == 1:
                # First call: email check (user doesn't exist)
                return check_response
            elif mock_execute.call_count == 2:
                # Second call: user insert
                return insert_response
            else:
                # Subsequent calls: refresh token insert
                return Mock(data=[{"token_id": 1}])
        
        mock_table.eq.return_value.execute = mock_execute
        
        # Override dependency
        app = client.app
        app.dependency_overrides[get_supabase_admin] = lambda: mock_supabase_client
        
        try:
            response = client.post("/api/auth/register", json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "role": "BUYER"
            })
            
            if response.status_code != status.HTTP_201_CREATED:
                print(f"Error: {response.status_code} - {response.json()}")
            
            assert response.status_code == status.HTTP_201_CREATED
            assert "access_token" in response.json()
            assert "refresh_token" in response.json()
            assert response.json()["user"]["email"] == "newuser@example.com"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_register_duplicate_email(self, client, mock_supabase_table, mock_supabase_client):
        """Test registration with duplicate email."""
        # Mock: user already exists
        check_response = Mock()
        check_response.data = [{"user_id": 1}]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = check_response
        
        response = client.post("/api/auth/register", json={
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "role": "BUYER"
        })
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_weak_password(self, client, mock_supabase_table):
        """Test registration with weak password."""
        response = client.post("/api/auth/register", json={
            "email": "weak@example.com",
            "password": "123",
            "username": "weakpass",
            "first_name": "Weak",
            "last_name": "Pass",
            "role": "BUYER"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_invalid_role(self, client, mock_supabase_client):
        """Test registration with invalid role."""
        check_response = Mock()
        check_response.data = []
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = check_response
        
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "INVALID_ROLE"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_all_roles(self, client, mock_supabase_table):
        """Test registration for all allowed roles."""
        roles = ["BUYER", "ORGANIZER", "SCANNER", "RESELLER"]
        
        for role in roles:
            # Reset mocks for each iteration
            mock_supabase_table.reset_mock()
            
            email_check = Mock()
            email_check.data = []
            
            user_insert = Mock()
            user_insert.data = [{"user_id": 1, "email": "test@example.com", "role": role}]
            
            refresh_insert = Mock()
            refresh_insert.data = [{"token_id": 1}]
            
            mock_supabase_table.execute.side_effect = [
                email_check,
                user_insert,
                refresh_insert
            ]
            
            response = client.post("/api/auth/register", json={
                "email": f"{role.lower()}@example.com",
                "password": "SecurePass123!",
                "username": f"{role.lower()}",
                "first_name": "Test",
                "last_name": "Role",
                "role": role
            })
            if response.status_code != status.HTTP_201_CREATED:
                print(f"Error: {response.status_code} - {response.json()}")
            
            assert response.status_code == status.HTTP_201_CREATED
            assert "access_token" in response.json()
            assert "refresh_token" in response.json()


class TestAuthLogin:
    """Test user login."""
    
    def test_login_success(self, client, mock_supabase_client, test_user):
        """Test successful login."""
        from auth_utils import verify_password
        
        # Mock database lookup
        response_mock = Mock()
        response_mock.data = [test_user]
        
        update_mock = Mock()
        update_mock.data = [test_user]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.side_effect = [
            response_mock,  # User lookup
            update_mock,    # Update failed attempts
            Mock(data=[{"token_id": 1}])  # Refresh token insert
        ]
        
        with patch("routers.auth.verify_password", return_value=True):
            response = client.post("/api/auth/login", json={
                "email": test_user["email"],
                "password": "secret"
            })
        
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
        assert response.json()["user"]["email"] == test_user["email"]
    
    def test_login_invalid_credentials(self, client, mock_supabase_client):
        """Test login with invalid credentials."""
        # Mock: user doesn't exist
        response_mock = Mock()
        response_mock.data = []
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = response_mock
        
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_wrong_password(self, client, mock_supabase_client, test_user):
        """Test login with wrong password."""
        response_mock = Mock()
        response_mock.data = [test_user]
        
        update_mock = Mock()
        update_mock.data = [test_user]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = response_mock
        mock_table.update.return_value.eq.return_value.execute.return_value = update_mock
        
        with patch("routers.auth.verify_password", return_value=False):
            response = client.post("/api/auth/login", json={
                "email": test_user["email"],
                "password": "wrongpassword"
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_account(self, client, mock_supabase_client):
        """Test login with inactive account."""
        inactive_user = {
            "user_id": 1,
            "email": "inactive@example.com",
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "role": "BUYER",
            "is_active": False,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        response_mock = Mock()
        response_mock.data = [inactive_user]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = response_mock
        
        response = client.post("/api/auth/login", json={
            "email": inactive_user["email"],
            "password": "secret"
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_login_locked_account(self, client, mock_supabase_client):
        """Test login with locked account."""
        future_lock = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        locked_user = {
            "user_id": 1,
            "email": "locked@example.com",
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "role": "BUYER",
            "locked_until": future_lock,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        response_mock = Mock()
        response_mock.data = [locked_user]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = response_mock
        
        response = client.post("/api/auth/login", json={
            "email": locked_user["email"],
            "password": "secret"
        })
        
        assert response.status_code == status.HTTP_423_LOCKED
    
    def test_login_account_lock_after_failed_attempts(self, client, mock_supabase_table, test_user):
        """Test account locking after failed attempts."""
        # Mock user found but password mismatch
        user_data = test_user.copy()
        user_data["failed_login_attempts"] = 5
        user_data["locked_until"] = "2025-12-31T23:59:59Z"
        
        mock_response = Mock()
        mock_response.data = [user_data]
        
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword123!"
        })
        assert response.status_code == status.HTTP_423_LOCKED


class TestAuthRefreshToken:
    """Test token refresh."""
    
    def test_refresh_token_success(self, client, mock_supabase_client, test_user):
        """Test successful token refresh."""
        from auth_utils import create_refresh_token, verify_token
        
        refresh_token = create_refresh_token(test_user["user_id"])
        
        token_record = {
            "token_id": 1,
            "token": refresh_token,
            "user_id": test_user["user_id"],
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "is_valid": True
        }
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.side_effect = [
            Mock(data=[token_record]),  # Token lookup
            Mock(data=[test_user]),     # User lookup
            Mock(data=[token_record])   # Token update
        ]
        
        with patch("routers.auth.verify_token", return_value={"sub": str(test_user["user_id"])}):
            response = client.post("/api/auth/refresh-token", json={
                "refresh_token": refresh_token
            })
        
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        with patch("routers.auth.verify_token", return_value=None):
            response = client.post("/api/auth/refresh-token", json={
                "refresh_token": "invalid_token"
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_not_in_db(self, client, mock_supabase_client):
        """Test refresh token not found in database."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[])
        
        with patch("routers.auth.verify_token", return_value={"sub": "1"}):
            response = client.post("/api/auth/refresh-token", json={
                "refresh_token": "valid_but_not_in_db"
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_expired(self, client, mock_supabase_client):
        """Test refresh with expired token."""
        expired_token = {
            "token_id": 1,
            "token": "expired_token",
            "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "is_valid": True
        }
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[expired_token])
        
        with patch("routers.auth.verify_token", return_value={"sub": "1"}):
            response = client.post("/api/auth/refresh-token", json={
                "refresh_token": "expired_token"
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthLogout:
    """Test logout functionality."""
    
    def test_logout_success(self, client, mock_supabase_client):
        """Test successful logout."""
        update_mock = Mock()
        update_mock.data = [{"is_valid": False}]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = update_mock
        
        response = client.post("/api/auth/logout", json={
            "refresh_token": "some_token"
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] == True


class TestAuthGetCurrentUser:
    """Test get current user endpoint."""
    
    def test_get_current_user_success(self, client, auth_headers, mock_supabase_client, test_user):
        """Test getting current user info."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[test_user])
        
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == test_user["email"]
        assert "password" not in response.json()
        assert "password_hash" not in response.json()
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthPasswordReset:
    """Test password reset functionality."""
    
    def test_forgot_password_success(self, client, mock_supabase_client, test_user):
        """Test forgot password request."""
        response_mock = Mock()
        response_mock.data = [test_user]
        
        update_mock = Mock()
        update_mock.data = [test_user]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = response_mock
        mock_table.update.return_value.eq.return_value.execute.return_value = update_mock
        
        response = client.post("/api/auth/forgot-password", json={
            "email": test_user["email"]
        })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_forgot_password_user_not_found(self, client, mock_supabase_client):
        """Test forgot password for non-existent user."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[])
        
        response = client.post("/api/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        
        # Should still return 200 to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK
    
    def test_reset_password_success(self, client, mock_supabase_client, test_user):
        """Test password reset."""
        from auth_utils import generate_token
        
        reset_token = generate_token()
        
        # Mock user lookup with reset token
        user_with_token = {
            **test_user,
            "reset_password_token": reset_token,
            "reset_password_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        response_mock = Mock()
        response_mock.data = [user_with_token]
        
        update_mock = Mock()
        update_mock.data = [user_with_token]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.side_effect = [
            response_mock,  # User lookup
            update_mock,    # Password update
            Mock(data=[])   # Token invalidation
        ]
        
        response = client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewSecurePass123!"
        })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_reset_password_invalid_token(self, client, mock_supabase_client):
        """Test password reset with invalid token."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[])
        
        response = client.post("/api/auth/reset-password", json={
            "token": "invalid_token",
            "new_password": "NewSecurePass123!"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_reset_password_expired_token(self, client, mock_supabase_client, test_user):
        """Test password reset with expired token."""
        user_with_expired_token = {
            **test_user,
            "reset_password_token": "expired_token",
            "reset_password_expires": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        }
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[user_with_expired_token])
        
        response = client.post("/api/auth/reset-password", json={
            "token": "expired_token",
            "new_password": "NewSecurePass123!"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuthVerifyEmail:
    """Test email verification."""
    
    def test_verify_email_success(self, client, mock_supabase_client, test_user):
        """Test successful email verification."""
        from auth_utils import generate_token
        
        verify_token = generate_token()
        user_with_token = {
            **test_user,
            "verification_token": verify_token,
            "verification_token_expires": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "is_email_verified": False
        }
        
        response_mock = Mock()
        response_mock.data = [user_with_token]
        
        update_mock = Mock()
        update_mock.data = [{**user_with_token, "is_email_verified": True}]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.side_effect = [
            response_mock,
            update_mock
        ]
        
        response = client.post("/api/auth/verify-email", json={
            "token": verify_token
        })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_verify_email_already_verified(self, client, mock_supabase_client, test_user):
        """Test verifying already verified email."""
        user_verified = {
            **test_user,
            "verification_token": "some_token",
            "is_email_verified": True
        }
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[user_verified])
        
        response = client.post("/api/auth/verify-email", json={
            "token": "some_token"
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert "already verified" in response.json()["message"].lower()
    
    def test_verify_email_invalid_token(self, client, mock_supabase_client):
        """Test email verification with invalid token."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[])
        
        response = client.post("/api/auth/verify-email", json={
            "token": "invalid_token"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_verify_email_expired_token(self, client, mock_supabase_client, test_user):
        """Test email verification with expired token."""
        user_with_expired = {
            **test_user,
            "verification_token": "expired_token",
            "verification_token_expires": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "is_email_verified": False
        }
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.eq.return_value.execute.return_value = Mock(data=[user_with_expired])
        
        response = client.post("/api/auth/verify-email", json={
            "token": "expired_token"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
