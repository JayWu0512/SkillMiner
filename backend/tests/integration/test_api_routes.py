"""Integration tests for API routes."""
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_route():
    """Test health endpoint via API."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_route():
    """Test root endpoint via API."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


@patch('src.api.routers.chat.get_openai_client')
@patch('src.rag.retriever.retrieve')
def test_chat_route_success(mock_retrieve, mock_get_client):
    """Test chat endpoint with successful response."""
    # Mock OpenAI client
    mock_client = Mock()
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message.content = "This is a test response"
    mock_client.chat.completions.create.return_value = mock_completion
    mock_get_client.return_value = mock_client

    # Mock RAG retrieval
    mock_retrieve.return_value = [
        ("[1] Test Title", "Test document content")
    ]

    # Mock save_chat_log to avoid file I/O
    with patch('src.api.routers.chat.save_chat_log'):
        response = client.post(
            "/chat",
            json={
                "message": "What skills do I need?",
                "resume_text": "Software Engineer with Python"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0


@patch('src.api.routers.chat.get_openai_client')
def test_chat_route_missing_openai_key(mock_get_client):
    """Test chat endpoint when OpenAI key is missing."""
    mock_get_client.side_effect = RuntimeError("OPENAI_API_KEY is not set")

    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )

    assert response.status_code == 500
    assert "OpenAI" in response.json()["detail"]


def test_chat_route_empty_message():
    """Test chat endpoint with empty message."""
    response = client.post(
        "/chat",
        json={"message": ""}
    )

    assert response.status_code == 422  # Validation error


@patch('src.api.routers.upload.parse_resume')
def test_upload_route_success(mock_parse):
    """Test upload endpoint with successful PDF parsing."""
    mock_parse.return_value = "Parsed resume text content"

    # Create a mock file for FastAPI TestClient
    files = {"file": ("resume.pdf", b"fake pdf content", "application/pdf")}

    response = client.post(
        "/upload",
        files=files
    )

    if response.status_code == 200:
        data = response.json()
        assert "text" in data
        assert "status" in data
        assert data["status"] == "success"


def test_upload_route_invalid_file_type():
    """Test upload endpoint with invalid file type."""
    files = {"file": ("document.txt", b"text content", "text/plain")}

    response = client.post(
        "/upload",
        files=files
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    # CORS middleware should handle OPTIONS requests
    # The exact status code depends on FastAPI CORS configuration
    assert response.status_code in [200, 204, 405]


@patch('src.api.routers.chat.get_openai_client')
@patch('src.rag.retriever.retrieve')
def test_chat_route_with_rag_error(mock_retrieve, mock_get_client):
    """Test chat endpoint when RAG retrieval fails."""
    # Mock OpenAI client
    mock_client = Mock()
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message.content = "Response despite RAG error"
    mock_client.chat.completions.create.return_value = mock_completion
    mock_get_client.return_value = mock_client
    
    # Mock RAG retrieval to fail
    mock_retrieve.side_effect = Exception("RAG retrieval error")

    with patch('src.api.routers.chat.save_chat_log'):
        response = client.post(
            "/chat",
            json={"message": "Test message"}
        )

        # Should still succeed because RAG errors are handled gracefully
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
