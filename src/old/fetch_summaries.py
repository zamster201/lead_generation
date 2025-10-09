import re
import requests
from pathlib import Path
from io import BytesIO

# PDF + DOCX support
from PyPDF2 import PdfReader
from docx import Document


def strip_html_tags(raw_html: str) -> str:
    """
    Remove HTML tags and collapse whitespace.
    """
    text = re.sub(r"<[^>]+>", " ", raw_html)  # drop tags
    text = re.sub(r"\s+", " ", text)          # collapse spaces
    return text.strip()


def extract_pdf(content: bytes) -> str:
    """
    Extract text from PDF bytes.
    """
    try:
        reader = PdfReader(BytesIO(content))
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return " ".join(texts)
    except Exception as e:
        return f"[ERROR parsing PDF: {e}]"


def extract_docx(content: bytes) -> str:
    """
    Extract text from DOCX bytes.
    """
    try:
        doc = Document(BytesIO(content))
        return " ".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"[ERROR parsing DOCX: {e}]"


def fetch_summary_text(url: str, max_chars: int = 5000) -> str:
    """
    Fetch and sanitize text from a SAM.gov summary/attachment URL.

    Args:
        url: The URL provided in the SAM.gov record.
        max_chars: Trim result so we don't overflow DB.

    Returns:
        Extracted text (truncated), or error string if failed.
    """
    if not url:
        return ""

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        ctype = resp.headers.get("Content-Type", "").lower()

        if "text/html" in ctype:
            text = strip_html_tags(resp.text)
        elif "text/plain" in ctype:
            text = resp.text
        elif "pdf" in ctype:
            text = extract_pdf(resp.content)
        elif "word" in ctype or "officedocument.wordprocessingml" in ctype:
            text = extract_docx(resp.content)
        else:
            return f"[UNSUPPORTED content type: {ctype}]"

        return text[:max_chars]

    except Exception as e:
        return f"[ERROR fetching {url}: {e}]"
