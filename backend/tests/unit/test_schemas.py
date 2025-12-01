"""Unit tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError
from src.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    AnalysisRequest,
    AnalysisResponse,
)


def test_chat_request_valid():
    """Test valid ChatRequest."""
    request = ChatRequest(message="Hello, how are you?")
    assert request.message == "Hello, how are you?"
    assert request.resume_text is None
    assert request.user_id is None


def test_chat_request_with_resume():
    """Test ChatRequest with resume text."""
    request = ChatRequest(
        message="What skills do I need?",
        resume_text="John Doe, Software Engineer"
    )
    assert request.message == "What skills do I need?"
    assert request.resume_text == "John Doe, Software Engineer"


def test_chat_request_empty_message():
    """Test ChatRequest with empty message raises error."""
    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_chat_request_whitespace_message():
    """Test ChatRequest with whitespace-only message is trimmed."""
    request = ChatRequest(message="   ")
    # Should be trimmed to empty, which should raise error
    # Actually, validator should raise error for empty after strip
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")


def test_chat_response():
    """Test ChatResponse."""
    response = ChatResponse(reply="Hello!")
    assert response.reply == "Hello!"
    assert response.citations == []


def test_chat_response_with_citations():
    """Test ChatResponse with citations."""
    response = ChatResponse(
        reply="Here's the answer",
        citations=["citation1", "citation2"]
    )
    assert response.reply == "Here's the answer"
    assert len(response.citations) == 2


def test_upload_response():
    """Test UploadResponse."""
    response = UploadResponse(text="Parsed resume text")
    assert response.text == "Parsed resume text"
    assert response.status == "success"
    assert "successfully" in response.message.lower()


def test_analysis_request_valid():
    """Test valid AnalysisRequest."""
    request = AnalysisRequest(
        resume_text="John Doe, Software Engineer with Python",
        job_description="Looking for a Python developer"
    )
    assert len(request.resume_text) >= 10
    assert len(request.job_description) >= 10


def test_analysis_request_too_short():
    """Test AnalysisRequest with too short text raises error."""
    with pytest.raises(ValidationError):
        AnalysisRequest(
            resume_text="short",
            job_description="Looking for developer"
        )


def test_analysis_response():
    """Test AnalysisResponse."""
    response = AnalysisResponse(
        analysis_id="test-id-123",
        match_score=85.5
    )
    assert response.analysis_id == "test-id-123"
    assert response.match_score == 85.5
    assert 0 <= response.match_score <= 100

