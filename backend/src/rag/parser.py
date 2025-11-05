from PyPDF2 import PdfReader

def parse_resume(pdf_file) -> str:
    """
    pdf_file: starlette UploadFile or file-like with .file attribute
    """
    if not pdf_file:
        return ""
    try:
        # FastAPI's UploadFile has a .file (SpooledTemporaryFile)
        reader = PdfReader(pdf_file.file)
        txt = []
        for page in reader.pages:
            t = page.extract_text() or ""
            txt.append(t)
        return "\n".join(txt).strip()
    except Exception as e:
        return f"(Note: could not parse PDF: {e})"
