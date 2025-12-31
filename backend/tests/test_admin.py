import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from main import app
from routers.admin_auth import require_admin_auth

@pytest.fixture
def mock_admin_auth():
    """Override admin auth dependency."""
    mock_admin = {"user_id": 1, "username": "admin", "role": "ADMIN"}
    app.dependency_overrides[require_admin_auth] = lambda: mock_admin
    yield mock_admin
    app.dependency_overrides = {}

@pytest.fixture(autouse=True)
def mock_soar():
    """Mock SOAR integration."""
    with patch("routers.admin.get_soar_integration") as mock_get_soar:
        mock_soar_instance = AsyncMock()
        mock_get_soar.return_value = mock_soar_instance
        yield mock_soar_instance

class TestAdminStats:
    """Test admin statistics endpoints."""

    def test_get_admin_stats(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test getting admin dashboard statistics."""
        # Mock responses for various counts
        users_response = Mock()
        users_response.count = 100
        
        alerts_24h = Mock()
        alerts_24h.count = 10
        
        critical_24h = Mock()
        critical_24h.count = 2
        
        alerts_7d = Mock()
        alerts_7d.count = 50
        
        alerts_30d = Mock()
        alerts_30d.count = 100
        
        banned_users = Mock()
        banned_users.count = 5
        
        banned_ips = Mock()
        banned_ips.count = 2
        
        mock_supabase_table.execute.side_effect = [
            users_response,
            alerts_24h,
            critical_24h,
            alerts_7d,
            alerts_30d,
            banned_users,
            banned_ips
        ]

        response = client.get("/api/admin/stats")

        assert response.status_code == 200
        stats = response.json()
        assert stats["total_users"] == 100
        assert stats["total_alerts_24h"] == 10
        assert stats["critical_alerts_24h"] == 2
        assert stats["system_health"] == "HEALTHY"


class TestAdminAlerts:
    """Test admin alert management."""

    def test_get_alerts(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test listing alerts."""
        mock_response = Mock()
        mock_response.data = [
            {
                "alert_id": 1,
                "user_id": 1,
                "ip_address": "127.0.0.1",
                "attack_type": "BRUTE_FORCE",
                "endpoint": "/login",
                "severity": "HIGH",
                "risk_score": 80,
                "status": "NEW",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_supabase_table.execute.return_value = mock_response

        response = client.get("/api/admin/alerts")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["attack_type"] == "BRUTE_FORCE"

    def test_get_alert_details(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test getting specific alert details."""
        alert_response = Mock()
        alert_response.data = [{
            "alert_id": 1,
            "user_id": 1,
            "ip_address": "127.0.0.1",
            "attack_type": "BRUTE_FORCE",
            "endpoint": "/login",
            "severity": "HIGH",
            "risk_score": 80,
            "status": "NEW",
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        user_alerts_response = Mock()
        user_alerts_response.count = 5
        
        mock_supabase_table.execute.side_effect = [alert_response, user_alerts_response]

        response = client.get("/api/admin/alerts/1")

        assert response.status_code == 200
        assert response.json()["alert_id"] == 1

    def test_update_alert_status(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test updating alert status."""
        admin_lookup_response = Mock()
        admin_lookup_response.data = [{"user_id": 1}]
        
        alert_check_response = Mock()
        alert_check_response.data = [{"alert_id": 1}]
        
        update_response = Mock()
        update_response.data = [{
            "alert_id": 1,
            "user_id": 1,
            "ip_address": "127.0.0.1",
            "attack_type": "BRUTE_FORCE",
            "endpoint": "/login",
            "severity": "HIGH",
            "risk_score": 80,
            "status": "REVIEWED",
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        mock_supabase_table.execute.side_effect = [
            admin_lookup_response,
            alert_check_response,
            update_response,
            Mock() # Log action
        ]

        response = client.patch(
            "/api/admin/alerts/1/status",
            json={"status": "REVIEWED"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "REVIEWED"

    def test_clear_all_alerts(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test clearing all alerts."""
        count_response = Mock()
        count_response.count = 10
        
        mock_supabase_table.execute.side_effect = [
            count_response, # Count before
            Mock(), # Delete
            Mock()  # Log action
        ]
        
        response = client.delete("/api/admin/alerts/clear")
        
        assert response.status_code == 200
        assert response.json()["deleted_count"] == 10


class TestAdminBans:
    """Test admin ban management."""

    def test_ban_user(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test banning a user."""
        ban_response = Mock()
        ban_response.data = [{"ban_id": 1}]
        
        mock_supabase_table.execute.side_effect = [
            ban_response, # Insert ban
            Mock(), # Update user is_active
            Mock()  # Log action
        ]

        response = client.post(
            "/api/admin/ban",
            json={
                "user_id": 1,
                "ban_reason": "Spam",
                "ban_duration": "PERMANENT"
            }
        )

        assert response.status_code == 200
        assert response.json()["success"] == True

    def test_unban_user(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test unbanning a user."""
        mock_supabase_table.execute.side_effect = [
            Mock(), # Update ban is_active
            Mock(), # Update user is_active
            Mock()  # Log action
        ]

        response = client.post(
            "/api/admin/unban",
            json={"user_id": 1}
        )

        assert response.status_code == 200
        assert response.json()["success"] == True


class TestAdminUsers:
    """Test admin user management."""

    def test_list_users(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test listing users."""
        mock_response = Mock()
        mock_response.data = [
            {
                "user_id": 1, 
                "email": "user1@example.com", 
                "role": "USER", 
                "is_active": True,
                "is_email_verified": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "user_id": 2, 
                "email": "user2@example.com", 
                "role": "ORGANIZER", 
                "is_active": True,
                "is_email_verified": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_supabase_table.execute.return_value = mock_response

        response = client.get("/api/admin/users")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_create_user(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test creating a new user."""
        # 1. Check email exists (empty)
        # 2. Insert user
        # 3. Log action
        
        check_email_response = Mock()
        check_email_response.data = []
        
        insert_response = Mock()
        insert_response.data = [{
            "user_id": 3,
            "email": "new@example.com",
            "username": "newuser",
            "role": "BUYER",
            "is_active": True,
            "is_email_verified": False,
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        mock_supabase_table.execute.side_effect = [
            check_email_response,
            insert_response,
            Mock()
        ]
        
        response = client.post(
            "/api/admin/users",
            json={
                "email": "new@example.com",
                "password": "Password123!",
                "username": "newuser",
                "role": "BUYER"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == "new@example.com"

    def test_update_user(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test updating a user."""
        update_response = Mock()
        update_response.data = [{
            "user_id": 1,
            "email": "updated@example.com",
            "role": "USER",
            "is_active": True,
            "is_email_verified": True,
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        mock_supabase_table.execute.side_effect = [
            update_response,
            Mock() # Log action
        ]
        
        response = client.patch(
            "/api/admin/users/1",
            json={"email": "updated@example.com"}
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == "updated@example.com"

    def test_delete_user(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test deleting a user."""
        get_user_response = Mock()
        get_user_response.data = [{"email": "delete@example.com"}]
        
        mock_supabase_table.execute.side_effect = [
            get_user_response,
            Mock(), # Delete
            Mock()  # Log action
        ]
        
        response = client.delete("/api/admin/users/1")
        
        assert response.status_code == 200
        assert response.json()["success"] == True

    def test_reset_user_password(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test resetting user password."""
        mock_supabase_table.execute.side_effect = [
            Mock(), # Update password
            Mock()  # Log action
        ]
        
        response = client.post(
            "/api/admin/users/1/reset-password",
            json={"user_id": 1, "new_password": "NewPassword123!"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] == True

    def test_get_user_activity(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test getting user activity."""
        activity_response = Mock()
        activity_response.data = [{"id": 1, "action": "LOGIN"}]
        
        # get_user_attack_count calls db.table("security_alerts")...
        attack_count_response = Mock()
        attack_count_response.count = 0
        
        mock_supabase_table.execute.side_effect = [
            activity_response,
            attack_count_response
        ]
        
        response = client.get("/api/admin/users/1/activity")
        
        assert response.status_code == 200
        assert len(response.json()["activity"]) == 1


class TestAdminWebRequests:
    """Test admin web requests management."""
    
    def test_get_web_requests(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test getting web requests."""
        # 1. Check table exists
        # 2. Count query
        # 3. Data query
        # 4. Log action
        
        check_table_response = Mock()
        check_table_response.data = [{"request_id": 1}]
        
        count_response = Mock()
        count_response.count = 10
        
        data_response = Mock()
        data_response.data = [{
            "request_id": 1,
            "user_id": 1,
            "ip_address": "127.0.0.1",
            "http_method": "GET",
            "path": "/api/test",
            "response_status": 200,
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        mock_supabase_table.execute.side_effect = [
            check_table_response,
            count_response,
            data_response,
            Mock()
        ]
        
        response = client.get("/api/admin/web-requests")
        
        assert response.status_code == 200
        assert response.json()["total"] == 10
        assert len(response.json()["results"]) == 1

    def test_export_web_requests(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test exporting web requests."""
        mock_response = Mock()
        mock_response.data = [{"request_id": 1, "path": "/test"}]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/admin/web-requests/export?format=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_clear_web_requests(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test clearing web requests."""
        delete_response = Mock()
        delete_response.data = [{"request_id": 1}]
        
        mock_supabase_table.execute.side_effect = [
            delete_response,
            Mock() # Log action
        ]
        
        response = client.delete("/api/admin/web-requests/clear")
        
        assert response.status_code == 200
        assert response.json()["success"] == True


class TestAdminSOAR:
    """Test admin SOAR configuration."""
    
    def test_create_soar_config(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test creating SOAR config."""
        insert_response = Mock()
        insert_response.data = [{"config_id": 1, "platform_name": "Test"}]
        
        mock_supabase_table.execute.side_effect = [
            insert_response,
            Mock() # Log action
        ]
        
        response = client.post(
            "/api/admin/soar/config",
            json={
                "platform_name": "Test",
                "endpoint_url": "http://test.com",
                "api_key": "secret"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["config_id"] == 1

    def test_get_soar_configs(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test getting SOAR configs."""
        mock_response = Mock()
        mock_response.data = [{"config_id": 1, "platform_name": "Test"}]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/admin/soar/config")
        
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_update_soar_config(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test updating SOAR config."""
        update_response = Mock()
        update_response.data = [{"config_id": 1, "platform_name": "Updated"}]
        
        mock_supabase_table.execute.side_effect = [
            update_response,
            Mock() # Log action
        ]
        
        response = client.patch(
            "/api/admin/soar/config/1",
            json={"platform_name": "Updated"}
        )
        
        assert response.status_code == 200
        assert response.json()["platform_name"] == "Updated"


class TestAdminGraphData:
    """Test admin graph data."""

    def test_get_graph_data(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test getting graph data."""
        mock_response = Mock()
        mock_response.data = [
            {"alert_id": 1, "attack_type": "BRUTE_FORCE", "severity": "HIGH", "created_at": "2024-01-01T10:00:00Z", "ip_address": "1.1.1.1", "endpoint": "/login"},
            {"alert_id": 2, "attack_type": "SQL_INJECTION", "severity": "CRITICAL", "created_at": "2024-01-01T11:00:00Z", "ip_address": "2.2.2.2", "endpoint": "/users"}
        ]
        mock_supabase_table.execute.return_value = mock_response

        response = client.get("/api/admin/graph-data")

        assert response.status_code == 200
        data = response.json()
        assert "alerts_by_type" in data
        assert "alerts_by_severity" in data
        assert data["alerts_by_type"]["BRUTE_FORCE"] == 1


class TestAdminExport:
    """Test admin export."""

    def test_export_alerts_json(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test exporting alerts as JSON."""
        mock_response = Mock()
        mock_response.data = [{"alert_id": 1, "attack_type": "TEST"}]
        mock_supabase_table.execute.return_value = mock_response

        response = client.get("/api/admin/export-alerts?format=json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_export_alerts_csv(self, client, mock_admin_auth, mock_supabase_client, mock_supabase_table):
        """Test exporting alerts as CSV."""
        mock_response = Mock()
        mock_response.data = [{"alert_id": 1, "attack_type": "TEST", "user_id": 1}]
        mock_supabase_table.execute.return_value = mock_response

        response = client.get("/api/admin/export-alerts?format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
