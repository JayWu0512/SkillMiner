"""Unit tests for PDF parser."""
from unittest.mock import Mock, patch
from src.rag.parser import parse_resume


def test_parse_resume_with_valid_pdf():
    """Test parsing a valid PDF file."""
    # Create a mock PDF file
    mock_pdf = Mock()
    mock_page = Mock()
    mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\nPython, SQL"
    mock_pdf.pages = [mock_page]

    mock_file = Mock()
    mock_file.file = mock_pdf

    with patch('src.rag.parser.PdfReader', return_value=mock_pdf):
        result = parse_resume(mock_file)
        assert isinstance(result, str)
        assert "John Doe" in result
        assert "Software Engineer" in result


def test_parse_resume_with_multiple_pages():
    """Test parsing a PDF with multiple pages."""
    mock_pdf = Mock()
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = Mock()
    mock_page2.extract_text.return_value = "Page 2 content"
    mock_pdf.pages = [mock_page1, mock_page2]

    mock_file = Mock()
    mock_file.file = mock_pdf

    with patch('src.rag.parser.PdfReader', return_value=mock_pdf):
        result = parse_resume(mock_file)
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "\n" in result  # Should join pages with newline


def test_parse_resume_with_empty_file():
    """Test parsing an empty/None file."""
    result = parse_resume(None)
    assert result == ""


def test_parse_resume_with_parsing_error():
    """Test that parser handles errors gracefully."""
    mock_file = Mock()
    mock_file.file = None

    with patch('src.rag.parser.PdfReader', side_effect=Exception("PDF parsing error")):
        result = parse_resume(mock_file)
        assert isinstance(result, str)
        assert "could not parse" in result.lower()
        assert "pdf parsing error" in result.lower()


def test_parse_resume_with_empty_pages():
    """Test parsing a PDF with empty pages."""
    mock_pdf = Mock()
    mock_page = Mock()
    mock_page.extract_text.return_value = None
    mock_pdf.pages = [mock_page]

    mock_file = Mock()
    mock_file.file = mock_pdf

    with patch('src.rag.parser.PdfReader', return_value=mock_pdf):
        result = parse_resume(mock_file)
        assert isinstance(result, str)
        # Should handle None gracefully
        assert result.strip() == "" or result == ""
