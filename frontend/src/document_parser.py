import io
import re
from typing import Optional
from pathlib import Path

import docx
import PyPDF2
import pdfplumber
from fastapi import UploadFile


class DocumentParser:
    """Handles parsing of PDF and DOCX resume files."""
    
    @staticmethod
    async def extract_text_from_upload(file: UploadFile) -> str:
        """Extract text from uploaded PDF or DOCX file."""
        content = await file.read()
        
        if file.filename.lower().endswith('.pdf'):
            return DocumentParser._extract_from_pdf(content)
        elif file.filename.lower().endswith(('.docx', '.doc')):
            return DocumentParser._extract_from_docx(content)
        else:
            raise ValueError(f"Unsupported file type: {file.filename}")
    
    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        """Extract text from PDF bytes using pdfplumber (more reliable than PyPDF2)."""
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
        except Exception:
            # Fallback to PyPDF2 if pdfplumber fails
            return DocumentParser._extract_from_pdf_pypdf2(content)
    
    @staticmethod
    def _extract_from_pdf_pypdf2(content: bytes) -> str:
        """Fallback PDF extraction using PyPDF2."""
        text = ""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    
    @staticmethod
    def _extract_from_docx(content: bytes) -> str:
        """Extract text from DOCX bytes."""
        doc = docx.Document(io.BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\-\(\)\+\#]', ' ', text)
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        return text.strip()