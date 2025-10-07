import requests
from PyPDF2 import PdfReader
from io import BytesIO
from typing import Optional

def parse_attachment(url: str) -> Optional[str]:
    """Download & extract text from PDF attachment URL (e.g., from SAM API)."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        reader = PdfReader(BytesIO(resp.content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"PDF parse error for {url}: {e}")
        return None

# Test stub (mock URL would need real fetch)
if __name__ == "__main__":
    # print(parse_attachment("https://example.gov/sample.pdf"))  # Uncomment with real URL
    pass