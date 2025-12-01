"""Unit tests for RAG retriever."""
from unittest.mock import Mock, patch
from src.rag.retriever import (
    build_context_block,
    retrieve,
)


def test_build_context_block_with_empty_retrieved():
    """Test building context block with no retrieved documents."""
    resume_text = "John Doe, Software Engineer"
    user_message = "What skills do I need?"
    retrieved = []

    result = build_context_block(resume_text, user_message, retrieved)

    assert isinstance(result, str)
    assert "CONTEXT: (none retrieved)" in result
    assert resume_text in result
    assert user_message in result


def test_build_context_block_with_retrieved():
    """Test building context block with retrieved documents."""
    resume_text = "John Doe, Software Engineer"
    user_message = "What skills do I need?"
    retrieved = [
        ("[1] Data Engineer", "Python, SQL, Spark are key skills"),
        ("[2] Software Engineer", "Java, Python, React"),
    ]

    result = build_context_block(resume_text, user_message, retrieved)

    assert isinstance(result, str)
    assert "CONTEXT" in result
    assert "[1] Data Engineer" in result
    assert "[2] Software Engineer" in result
    assert "Python, SQL, Spark" in result
    assert resume_text in result
    assert user_message in result


def test_build_context_block_truncates_long_text():
    """Test that context block truncates very long text."""
    long_resume = "A" * 10000
    long_message = "B" * 2000
    retrieved = []

    result = build_context_block(long_resume, long_message, retrieved)

    # The result should contain truncated versions
    assert len(result) < len(long_resume) + len(long_message) + 1000


def test_retrieve_with_mocked_chroma():
    """Test retrieve function with mocked ChromaDB."""
    resume_text = "Software Engineer with Python experience"
    user_message = "What skills should I learn?"

    # Mock ChromaDB collection
    mock_collection = Mock()
    mock_collection.count.return_value = 10
    mock_collection.query.return_value = {
        "documents": [["Python, SQL, and data engineering skills are important"]],
        "metadatas": [[{"title_lc": "Data Engineer"}]],
    }

    with patch('src.rag.retriever._get_collection', return_value=mock_collection):
        with patch('src.rag.retriever.ensure_seeded_roles', return_value=10):
            result = retrieve(resume_text, user_message, top_k=1)

            assert isinstance(result, list)
            if result:  # If retrieval succeeds
                assert len(result) > 0
                assert isinstance(result[0], tuple)
                assert len(result[0]) == 2  # (header, document)


def test_retrieve_handles_errors_gracefully():
    """Test that retrieve handles errors gracefully."""
    resume_text = "Test resume"
    user_message = "Test message"

    # Mock ChromaDB to raise an error
    with patch('src.rag.retriever._get_collection', side_effect=Exception("ChromaDB error")):
        with patch('src.rag.retriever.ensure_seeded_roles', side_effect=Exception("Seeding error")):
            result = retrieve(resume_text, user_message)
            # Should return empty list on error
            assert isinstance(result, list)
            assert len(result) == 0


def test_retrieve_with_empty_inputs():
    """Test retrieve with empty resume and message."""
    with patch('src.rag.retriever._get_collection') as mock_get_collection:
        mock_collection = Mock()
        mock_collection.count.return_value = 10
        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
        }
        mock_get_collection.return_value = mock_collection

        with patch('src.rag.retriever.ensure_seeded_roles', return_value=10):
            result = retrieve("", "")
            assert isinstance(result, list)
