import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    response = client.get("/api/chatbot/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

@patch("routers.chatbot.model")
def test_send_message(mock_model):
    # Mock the chat session and response
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello! I am Gemini."
    mock_chat.send_message.return_value = mock_response
    mock_model.start_chat.return_value = mock_chat

    response = client.post(
        "/api/chatbot/send",
        json={"message": "Hi", "session_id": "test_session"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello! I am Gemini."
    assert data["session_id"] == "test_session"
    assert "timestamp" in data

@patch("routers.chatbot.model", None)
def test_send_message_no_api_key():
    response = client.post(
        "/api/chatbot/send",
        json={"message": "Hi"}
    )
    assert response.status_code == 503
    assert "Chatbot service unavailable" in response.json()["detail"]
